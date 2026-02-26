from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import yaml
from cosf.parser.workflow import WorkflowParser
from cosf.engine.runtime import ExecutionEngine
from cosf.engine.adapter import AdapterRegistry
from cosf.engine.loader import load_adapters
from cosf.models.database import WorkflowExecution
from cosf.models.db_session import AsyncSessionLocal, init_db
from sqlalchemy import select
from sqlalchemy.orm import selectinload

app = FastAPI(title="COSF Control Plane API", version="0.1.0")

class WorkflowRunRequest(BaseModel):
    workflow_yaml: str

class ExecutionStatus(BaseModel):
    id: str
    workflow_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None

def get_engine():
    registry = AdapterRegistry()
    load_adapters(registry)
    return ExecutionEngine(adapter_registry=registry)

async def run_workflow_task(execution_id: str, workflow_yaml: str):
    """Background task to execute a workflow."""
    parser = WorkflowParser()
    workflow = parser.parse(workflow_yaml)
    engine = get_engine()
    
    # Note: In a real enterprise system, we'd want to correlate the background task
    # with the already created WorkflowExecution record. For now, we let engine.run
    # create its own record as it does currently, but we'll improve this in Phase 2.
    await engine.run(workflow)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "COSF API is running", "version": "0.1.0"}

@app.post("/workflows/run", status_code=202)
async def run_workflow(request: WorkflowRunRequest, background_tasks: BackgroundTasks):
    """Triggers a security workflow execution in the background."""
    try:
        # Validate YAML first
        yaml.safe_load(request.workflow_yaml)
        
        # In Phase 1, we just fire and forget. 
        # In Phase 2, we will create the DB record here and return its ID.
        background_tasks.add_task(run_workflow_task, "pending", request.workflow_yaml)
        return {"message": "Workflow execution triggered", "status": "accepted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid workflow: {str(e)}")

@app.get("/executions", response_model=List[ExecutionStatus])
async def list_executions():
    """Lists all historical workflow executions."""
    async with AsyncSessionLocal() as session:
        stmt = select(WorkflowExecution).order_by(WorkflowExecution.start_time.desc())
        result = await session.execute(stmt)
        executions = result.scalars().all()
        
        return [
            ExecutionStatus(
                id=e.id,
                workflow_name=e.workflow_name,
                status=e.status,
                start_time=e.start_time.isoformat(),
                end_time=e.end_time.isoformat() if e.end_time else None
            ) for e in executions
        ]

@app.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Returns details of a specific execution."""
    async with AsyncSessionLocal() as session:
        stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id).options(selectinload(WorkflowExecution.tasks))
        result = await session.execute(stmt)
        execution = result.scalar_one_or_none()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
            
        return {
            "id": execution.id,
            "workflow_name": execution.workflow_name,
            "status": execution.status,
            "tasks": [
                {
                    "name": t.task_name,
                    "adapter": t.adapter,
                    "status": t.status,
                    "error": t.error
                } for t in execution.tasks
            ]
        }
