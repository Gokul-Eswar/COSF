from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))  # pending, running, completed, failed
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    tasks: Mapped[List["TaskExecution"]] = relationship(back_populates="execution", cascade="all, delete-orphan")

class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(ForeignKey("workflow_executions.id"))
    task_name: Mapped[str] = mapped_column(String(255))
    adapter: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    execution: Mapped["WorkflowExecution"] = relationship(back_populates="tasks")

class DBAsset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(50))
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class DBService(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"))
    port: Mapped[int] = mapped_column(Integer)
    protocol: Mapped[str] = mapped_column(String(20))
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
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
