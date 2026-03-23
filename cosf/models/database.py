from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))  # pending, running, completed, failed
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    public_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    tasks: Mapped[List["TaskExecution"]] = relationship(back_populates="execution", cascade="all, delete-orphan")

class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(ForeignKey("workflow_executions.id"))
    task_name: Mapped[str] = mapped_column(String(255))
    adapter: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_output: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    execution: Mapped["WorkflowExecution"] = relationship(back_populates="tasks")

class DBAsset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(50))
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

class DBService(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"))
    port: Mapped[int] = mapped_column(Integer)
    protocol: Mapped[str] = mapped_column(String(20))
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

class DBVulnerability(Base):
    __tablename__ = "vulnerabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"))
    cve_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    severity: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String)
    remediation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    service_id: Mapped[Optional[str]] = mapped_column(ForeignKey("services.id"), nullable=True)

class DBCredential(Base):
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[Optional[str]] = mapped_column(ForeignKey("assets.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(255))
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    source_task_id: Mapped[Optional[str]] = mapped_column(ForeignKey("task_executions.id"), nullable=True)

class DBAttackStep(Base):
    __tablename__ = "attack_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String)
    technique_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    evidence_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class DBEvidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String)
    hash_sha256: Mapped[str] = mapped_column(String(64))
    task_id: Mapped[Optional[str]] = mapped_column(ForeignKey("task_executions.id"), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class DBRelationship(Base):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id: Mapped[str] = mapped_column(String(36)) # Could be Asset ID, Service ID, etc.
    target_id: Mapped[str] = mapped_column(String(36))
    type: Mapped[str] = mapped_column(String(100))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class DBWorkflowDraft(Base):
    __tablename__ = "workflow_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[dict] = mapped_column(JSON) # Stores the visual layout/tasks
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
