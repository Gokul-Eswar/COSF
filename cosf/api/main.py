from fastapi import FastAPI, BackgroundTasks, HTTPException, Body, Depends, Security, Query
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
from redis import Redis
from rq import Queue

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
from cosf.models.database import WorkflowExecution, DBAsset, DBVulnerability, DBWorkflowDraft
from cosf.models.db_session import AsyncSessionLocal, init_db
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from cosf.engine.graph import GraphEngine
from cosf.engine.intelligence import InferenceEngine

app = FastAPI(title="COSF Control Plane API", version="0.2.0")

# ... existing Auth & RBAC ...

class WorkflowDraftCreate(BaseModel):
    name: str
    description: Optional[str] = None
    content: Dict[str, Any]

@app.get("/api/adapters")
async def list_adapters_metadata(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns metadata about all registered tool adapters for the visual builder."""
    registry = AdapterRegistry()
    load_adapters(registry)
    adapters = registry.list_adapters()
    
    return [
        {
            "id": name,
            "name": adapter.ADAPTER_NAME,
            "description": adapter.ADAPTER_DESCRIPTION,
            "params_schema": {} # Future: Add JSON schema for params
        } for name, adapter in adapters.items()
    ]

@app.get("/api/drafts")
async def list_drafts(user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all saved workflow drafts."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBWorkflowDraft).order_by(DBWorkflowDraft.updated_at.desc())
        result = await session.execute(stmt)
        drafts = result.scalars().all()
        return drafts

@app.post("/api/drafts", status_code=201)
async def create_draft(request: WorkflowDraftCreate, user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))):
    """Saves a new workflow draft."""
    async with AsyncSessionLocal() as session:
        new_draft = DBWorkflowDraft(
            name=request.name,
            description=request.description,
            content=request.content
        )
        session.add(new_draft)
        await session.commit()
        await session.refresh(new_draft)
        return new_draft

@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves a specific workflow draft."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBWorkflowDraft).where(DBWorkflowDraft.id == draft_id)
        draft = (await session.execute(stmt)).scalar_one_or_none()
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        return draft

@app.put("/api/drafts/{draft_id}")
async def update_draft(draft_id: str, request: WorkflowDraftCreate, user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))):
    """Updates an existing workflow draft."""
    async with AsyncSessionLocal() as session:
        stmt = update(DBWorkflowDraft).where(DBWorkflowDraft.id == draft_id).values(
            name=request.name,
            description=request.description,
            content=request.content,
            updated_at=datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Draft not found")
        await session.commit()
        return {"message": "Draft updated"}

@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str, user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))):
    """Deletes a workflow draft."""
    async with AsyncSessionLocal() as session:
        stmt = delete(DBWorkflowDraft).where(DBWorkflowDraft.id == draft_id)
        result = await session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Draft not found")
        await session.commit()
        return {"message": "Draft deleted"}

@app.post("/api/drafts/{draft_id}/export")
async def export_draft_to_wdl(draft_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Converts a visual draft to WDL YAML."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBWorkflowDraft).where(DBWorkflowDraft.id == draft_id)
        draft = (await session.execute(stmt)).scalar_one_or_none()
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Mapping logic: visual content -> WDL schema
        # Assuming draft.content has 'tasks' and 'name'
        wdl_data = {
            "name": draft.name,
            "description": draft.description or "",
            "version": "1.0",
            "tasks": draft.content.get("tasks", [])
        }
        
        yaml_output = yaml.dump(wdl_data, sort_keys=False)
        return {"workflow_yaml": yaml_output}

# ... existing code ...
