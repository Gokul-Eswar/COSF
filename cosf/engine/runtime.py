import asyncio
from datetime import datetime
from typing import List, Any, Dict, Optional
from cosf.parser.workflow import WorkflowSchema, WorkflowTask
from cosf.engine.adapter import AdapterRegistry
from cosf.models.database import WorkflowExecution, TaskExecution, DBAsset, DBService, DBVulnerability
from cosf.models.db_session import AsyncSessionLocal, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from cosf.models.som import Asset, Service, Vulnerability

class ExecutionEngine:
    """The core engine for orchestrating and executing security workflows.

    The ExecutionEngine manages the sequential execution of tasks defined in a
    WorkflowSchema, utilizing registered adapters to perform the actual work.
    """

    def __init__(self, adapter_registry: AdapterRegistry = None):
        """Initializes the execution engine.

        Args:
            adapter_registry: An optional AdapterRegistry instance. If not
                provided, a new empty registry is created.
        """
        self.adapters = adapter_registry or AdapterRegistry()

    async def run(self, workflow: WorkflowSchema):
        """Executes a complete security workflow.

        Iterates through the tasks in the workflow and executes them sequentially.
        If a task fails, the workflow execution is halted.

        Args:
            workflow: The WorkflowSchema to execute.

        Raises:
            Exception: If any task execution fails.
        """
        await init_db()
        async with AsyncSessionLocal() as session:
            db_exec = WorkflowExecution(
                workflow_name=workflow.name,
                status="running",
                start_time=datetime.utcnow()
            )
            session.add(db_exec)
            await session.commit()
            await session.refresh(db_exec)

            print(f"Starting workflow: {workflow.name} (Execution ID: {db_exec.id})")
            
            try:
                for task in workflow.tasks:
                    await self.execute_task_in_context(task, db_exec.id, session)
                
                db_exec.status = "completed"
            except Exception as e:
                db_exec.status = "failed"
                print(f"Workflow stopped due to failure: {e}")
                raise e
            finally:
                db_exec.end_time = datetime.utcnow()
                await session.commit()
                print(f"Workflow {db_exec.status}: {workflow.name}")

    async def execute_task_in_context(self, task: WorkflowTask, execution_id: str, session: AsyncSession):
        """Executes a task and records its history."""
        db_task = TaskExecution(
            execution_id=execution_id,
            task_name=task.name,
            adapter=task.adapter,
            status="running",
            start_time=datetime.utcnow()
        )
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)

        print(f"Executing task: {task.name} with adapter: {task.adapter}")
        try:
            adapter = self.adapters.get(task.adapter)
            result = await adapter.run(task.params)
            
            db_task.status = "completed"
            db_task.end_time = datetime.utcnow()
            
            # If result is a SOM object or list of SOM objects, persist them
            if isinstance(result, list):
                db_task.result_json = [self._som_to_dict(r) for r in result]
                for item in result:
                    await self._persist_som_object(item, session)
            else:
                db_task.result_json = self._som_to_dict(result)
                await self._persist_som_object(result, session)
                
            await session.commit()
            return result
        except Exception as e:
            db_task.status = "failed"
            db_task.end_time = datetime.utcnow()
            db_task.error = str(e)
            await session.commit()
            raise e

    def _som_to_dict(self, obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode='json')
        return obj

    async def _persist_som_object(self, obj: Any, session: AsyncSession):
        """Persists a SOM object into the database if it matches known models."""
        if isinstance(obj, Asset):
            db_asset = DBAsset(
                id=obj.id,
                name=obj.name,
                ip_address=str(obj.ip_address),
                os=obj.os,
                tags={"tags": obj.tags}
            )
            await session.merge(db_asset)
        elif isinstance(obj, Service):
            db_service = DBService(
                id=obj.id,
                asset_id=obj.asset_id,
                port=obj.port,
                protocol=obj.protocol,
                name=obj.name,
                state=obj.state
            )
            await session.merge(db_service)
        elif isinstance(obj, Vulnerability):
            db_vuln = DBVulnerability(
                id=obj.id,
                asset_id=obj.asset_id,
                cve_id=obj.cve_id,
                severity=obj.severity,
                description=obj.description,
                remediation=obj.remediation,
                service_id=obj.service_id
            )
            await session.merge(db_vuln)

    async def execute_task(self, task: WorkflowTask) -> Any:
        """Executes a single workflow task using the appropriate adapter.
        Note: This is now a wrapper around execute_task_in_context for compatibility.
        """
        # For standalone task execution, we don't have a workflow context
        # But for 'cosf run' we use 'run' which calls 'execute_task_in_context'
        adapter = self.adapters.get(task.adapter)
        return await adapter.run(task.params)
