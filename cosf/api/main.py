from fastapi import FastAPI, BackgroundTasks, HTTPException, Body, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio

# ... existing imports ...

@app.get("/api/executions/{execution_id}/logs")
async def stream_execution_logs(execution_id: str, user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))):
    """Streams real-time execution logs via SSE."""
    from cosf.engine.runtime import ExecutionEngine
    
    async def log_generator():
        queue = ExecutionEngine.subscribe_logs(execution_id)
        try:
            while True:
                log_msg = await queue.get()
                yield f"data: {log_msg}\n\n"
                # Check if execution finished to close stream? 
                # For now, we rely on the client closing it or the queue being deleted.
        except asyncio.CancelledError:
            ExecutionEngine.unsubscribe_logs(execution_id, queue)
            raise

    return StreamingResponse(log_generator(), media_type="text/event-stream")
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
from cosf.engine.intelligence import InferenceEngine

app = FastAPI(title="COSF Control Plane API", version="0.2.0")

# --- Authentication & RBAC ---
API_KEY_NAME = "X-COSF-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

USER_DATABASE = {
    "admin-key-123": {"name": "Admin User", "role": "admin"},
    "operator-key-456": {"name": "Operator User", "role": "operator"},
    "readonly-key-789": {"name": "Auditor User", "role": "readonly"}
}

async def get_current_user(
    api_key: str = Security(api_key_header),
    token: Optional[str] = None
):
    actual_key = api_key or token
    if not actual_key:
        raise HTTPException(status_code=401, detail="API Key missing")
    user = USER_DATABASE.get(actual_key)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return user

def require_role(allowed_roles: List[str]):
    async def role_dependency(user: Dict[str, Any] = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Operation restricted to roles: {', '.join(allowed_roles)}")
        return user
    return role_dependency

# --- End Auth ---

# Setup paths for templates
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

class WorkflowRunRequest(BaseModel):
    workflow_yaml: str
    dry_run: bool = False

class WorkflowGenerationRequest(BaseModel):
    prompt: str
    provider: Optional[str] = "ollama"

class WorkflowGenerationResponse(BaseModel):
    workflow_yaml: str
    workflow_name: str

class PathValidationRequest(BaseModel):
    path: List[str]

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
    return {"message": "COSF API is running", "version": "0.2.0"}

@app.post("/workflows/run", status_code=202)
async def run_workflow(
    request: WorkflowRunRequest, 
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    """Triggers a security workflow execution in the background."""
    try:
        yaml.safe_load(request.workflow_yaml)
        background_tasks.add_task(run_workflow_task, "pending", request.workflow_yaml, dry_run=request.dry_run)
        return {
            "message": f"Workflow execution triggered {'(DRY RUN)' if request.dry_run else ''}", 
            "status": "accepted",
            "triggered_by": user["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid workflow: {str(e)}")

@app.get("/executions", response_model=List[ExecutionStatus])
async def list_executions(user: Dict[str, Any] = Depends(get_current_user)):
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
async def get_execution(execution_id: str, user: Dict[str, Any] = Depends(get_current_user)):
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
async def get_graph(infer: bool = True, user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the full security relationship graph."""
    engine = GraphEngine()
    await engine.build_from_db(infer=infer)
    return engine.get_graph_data()

@app.post("/api/analysis/critical-paths")
async def analyze_paths(user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))):
    """Triggers an autonomous attack path analysis."""
    engine = GraphEngine()
    await engine.build_from_db(infer=True)
    return engine.analyze_critical_paths()

@app.post("/api/analysis/preview-validation")
async def preview_validation(
    request: PathValidationRequest, 
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    """Generates a validation workflow for an attack path but does not run it."""
    engine = GraphEngine()
    await engine.build_from_db(infer=True)
    
    intel = InferenceEngine()
    entities = {"vulnerabilities": [], "assets": []} 
    
    async with AsyncSessionLocal() as session:
        from cosf.models.som import Vulnerability, Asset
        v_res = await session.execute(select(DBVulnerability))
        entities["vulnerabilities"] = [Vulnerability(id=v.id, asset_id=v.asset_id, cve_id=v.cve_id) for v in v_res.scalars()]
        a_res = await session.execute(select(DBAsset))
        entities["assets"] = [Asset(id=a.id, name=a.name, ip_address=a.ip_address) for a in a_res.scalars()]

    workflow = intel.validate_attack_path(request.path, entities)
    if not workflow:
        raise HTTPException(status_code=400, detail="Could not generate validation workflow for this path.")
    
    return {"workflow_yaml": yaml.dump(workflow.model_dump()), "workflow_name": workflow.name}

@app.post("/api/analysis/validate-path")
async def validate_path(
    request: PathValidationRequest, 
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    """Generates and triggers a validation workflow for a selected attack path."""
    engine = GraphEngine()
    await engine.build_from_db(infer=True)
    
    # We need to pass entities to the validator. 
    # For now, we'll fetch them again or use a better way.
    intel = InferenceEngine()
    # Mock entities for POC validation logic
    # In a real system, these would be loaded from DB
    entities = {"vulnerabilities": [], "assets": []} 
    
    async with AsyncSessionLocal() as session:
        from cosf.models.som import Vulnerability, Asset
        v_res = await session.execute(select(DBVulnerability))
        entities["vulnerabilities"] = [Vulnerability(id=v.id, asset_id=v.asset_id, cve_id=v.cve_id) for v in v_res.scalars()]
        a_res = await session.execute(select(DBAsset))
        entities["assets"] = [Asset(id=a.id, name=a.name, ip_address=a.ip_address) for a in a_res.scalars()]

    workflow = intel.validate_attack_path(request.path, entities)
    if not workflow:
        raise HTTPException(status_code=400, detail="Could not generate validation workflow for this path.")
    
    # Convert WorkflowSchema to YAML for run_workflow_task
    # Actually, run_workflow_task expects YAML, but we can update it or handle it here
    workflow_yaml = yaml.dump(workflow.model_dump())
    background_tasks.add_task(run_workflow_task, "pending", workflow_yaml, dry_run=False)
    
    return {"message": "Autonomous validation triggered", "workflow_name": workflow.name}

@app.get("/assets")
async def list_assets(user: Dict[str, Any] = Depends(get_current_user)):
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

@app.get("/api/assets/{asset_id}")
async def get_asset_details(asset_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Returns full details of a specific asset, including its services and vulnerabilities."""
    async with AsyncSessionLocal() as session:
        from cosf.models.database import DBService, DBVulnerability
        # Fetch asset
        stmt = select(DBAsset).where(DBAsset.id == asset_id)
        asset = (await session.execute(stmt)).scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Fetch services
        s_stmt = select(DBService).where(DBService.asset_id == asset_id)
        services = (await session.execute(s_stmt)).scalars().all()
        
        # Fetch vulnerabilities
        v_stmt = select(DBVulnerability).where(DBVulnerability.asset_id == asset_id)
        vulns = (await session.execute(v_stmt)).scalars().all()

        # Fetch evidence/raw outputs linked to this asset via tasks
        # (This is a bit more complex, for now we return basic info)
        
        return {
            "id": asset.id,
            "name": asset.name,
            "ip": asset.ip_address,
            "os": asset.os,
            "risk_score": asset.risk_score,
            "tags": asset.tags,
            "services": [
                {
                    "id": s.id,
                    "port": s.port,
                    "protocol": s.protocol,
                    "name": s.name,
                    "version": s.version
                } for s in services
            ],
            "vulnerabilities": [
                {
                    "id": v.id,
                    "cve": v.cve_id,
                    "severity": v.severity,
                    "description": v.description
                } for v in vulns
            ]
        }

@app.get("/api/vulnerabilities/{vuln_id}")
async def get_vulnerability_details(vuln_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Returns details of a specific vulnerability."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBVulnerability).where(DBVulnerability.id == vuln_id)
        vuln = (await session.execute(stmt)).scalar_one_or_none()
        if not vuln:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        return {
            "id": vuln.id,
            "cve": vuln.cve_id,
            "severity": vuln.severity,
            "description": vuln.description,
            "remediation": vuln.remediation
        }

@app.post("/api/ai/generate", response_model=WorkflowGenerationResponse)
async def generate_workflow_ai(
    request: WorkflowGenerationRequest,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    """Generates a security workflow from a natural language prompt using AI."""
    from cosf.ai.prompts import PromptManager
    from cosf.ai.engine import GenerativeEngine
    
    registry = AdapterRegistry()
    load_adapters(registry)
    
    prompt_mgr = PromptManager(registered_adapters=registry.list_adapters())
    # Use environment variable for API key if provided
    api_key = os.getenv("OPENAI_API_KEY")
    ai_engine = GenerativeEngine(prompt_manager=prompt_mgr, provider=request.provider, api_key=api_key)
    
    try:
        yaml_content = await ai_engine.generate_workflow(request.prompt)
        validated_schema = ai_engine.validate_generated_yaml(yaml_content)
        return WorkflowGenerationResponse(
            workflow_yaml=yaml_content,
            workflow_name=validated_schema.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")
