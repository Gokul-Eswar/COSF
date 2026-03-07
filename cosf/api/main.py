from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import yaml
import os
from pathlib import Path
from cosf.parser.workflow import WorkflowParser
from cosf.engine.runtime import ExecutionEngine
from cosf.engine.adapter import AdapterRegistry
from cosf.engine.loader import load_adapters
from cosf.models.database import WorkflowExecution, DBAsset, DBVulnerability
from cosf.models.db_session import AsyncSessionLocal, init_db
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from cosf.engine.graph import GraphEngine

app = FastAPI(title="COSF Control Plane API", version="0.1.0")

# Setup paths for templates
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

class WorkflowRunRequest(BaseModel):
    workflow_yaml: str
    dry_run: bool = False

class ExecutionStatus(BaseModel):
    id: str
    workflow_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None

_engine_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        registry = AdapterRegistry()
        load_adapters(registry)
        _engine_instance = ExecutionEngine(adapter_registry=registry)
    return _engine_instance

async def run_workflow_task(execution_id: str, workflow_yaml: str, dry_run: bool = False):
    """Background task to execute a workflow."""
    parser = WorkflowParser()
    workflow = parser.parse(workflow_yaml)
    engine = get_engine()
    await engine.run(workflow, dry_run=dry_run)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serves the main Command Center dashboard."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        return "<h1>Dashboard template not found.</h1>"
    return index_path.read_text()

@app.get("/api/health")
async def root():
    return {"message": "COSF API is running", "version": "0.1.0"}

@app.post("/workflows/run", status_code=202)
async def run_workflow(request: WorkflowRunRequest, background_tasks: BackgroundTasks):
    """Triggers a security workflow execution in the background."""
    try:
        yaml.safe_load(request.workflow_yaml)
        background_tasks.add_task(run_workflow_task, "pending", request.workflow_yaml, dry_run=request.dry_run)
        return {"message": f"Workflow execution triggered {'(DRY RUN)' if request.dry_run else ''}", "status": "accepted"}
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

@app.get("/graph")
async def get_graph(infer: bool = True):
    """Returns the full security relationship graph."""
    engine = GraphEngine()
    await engine.build_from_db(infer=infer)
    return engine.get_graph_data()

@app.get("/assets")
async def list_assets():
    """Returns all assets with their current risk scores."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBAsset).order_by(DBAsset.risk_score.desc())
        result = await session.execute(stmt)
        assets = result.scalars().all()
        
        return [
            {
                "id": a.id,
                "name": a.name,
                "ip": a.ip_address,
                "risk_score": a.risk_score,
                "tags": a.tags
            } for a in assets
        ]
