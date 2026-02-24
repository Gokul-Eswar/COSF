import asyncio
import re
from datetime import datetime, timezone
from typing import List, Any, Dict, Optional, Set
from cosf.parser.workflow import WorkflowSchema, WorkflowTask
from cosf.engine.adapter import AdapterRegistry, TaskResult
from cosf.models.database import WorkflowExecution, TaskExecution, DBAsset, DBService, DBVulnerability
from cosf.models.db_session import AsyncSessionLocal, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from cosf.models.som import Asset, Service, Vulnerability

class ConditionEvaluator:
    """Evaluates conditional 'when' expressions against the execution context."""

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def evaluate(self, condition: Optional[str]) -> bool:
        if not condition:
            return True
        
        # 1. Resolve variables first (e.g., {{ tasks.ID.outputs.KEY }})
        resolved = self._resolve_variables(condition).strip()
        
        # 2. Basic expression parsing (for now supporting ==, !=, contains, in)
        try:
            # Handle direct booleans
            if resolved.lower() == "true": return True
            if resolved.lower() == "false": return False

            # Match: "left_val" OPERATOR "right_val"
            # Support: ==, !=, contains, in
            pattern = r"^(.*?)\s+(==|!=|contains|in)\s+(.*)$"
            match = re.match(pattern, resolved)
            
            if not match:
                # Fallback: check if it's just a variable that resolved to a boolean string
                return resolved.lower() in ("true", "1", "yes")

            left, op, right = match.groups()
            left = self._strip_quotes(left)
            right = self._strip_quotes(right)

            if op == "==":
                return str(left) == str(right)
            elif op == "!=":
                return str(left) != str(right)
            elif op == "contains":
                # "left contains right" -> is right a substring of left?
                return str(right) in str(left)
            elif op == "in":
                # "left in right" -> is left a substring of right?
                return str(left) in str(right)
            
            return False
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False

    def _strip_quotes(self, s: str) -> str:
        s = s.strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            return s[1:-1]
        return s

    def _resolve_variables(self, expression: str) -> str:
        """Recursively resolves {{ tasks.ID.outputs.KEY }} in expression."""
        pattern = r"\{\{\s*tasks\.(\w+)\.outputs\.(\w+)\s*\}\}"
        matches = re.findall(pattern, expression)
        for task_id, key in matches:
            val = self.context.get("tasks", {}).get(task_id, {}).get("outputs", {}).get(key)
            if val is not None:
                expression = expression.replace(f"{{{{ tasks.{task_id}.outputs.{key} }}}}", str(val))
            else:
                # If variable not found, replace with 'None' or empty to avoid parsing issues
                expression = expression.replace(f"{{{{ tasks.{task_id}.outputs.{key} }}}}", "None")
        return expression

class ExecutionEngine:
    """The core engine for orchestrating and executing security workflows.

    The ExecutionEngine manages the execution of tasks defined in a
    WorkflowSchema, supporting dependencies, variable passing, retries, and timeouts.
    """

    def __init__(self, adapter_registry: AdapterRegistry = None):
        """Initializes the execution engine."""
        self.adapters = adapter_registry or AdapterRegistry()
        self.context: Dict[str, Any] = {}

    async def run(self, workflow: WorkflowSchema):
        """Executes a complete security workflow with dependency resolution."""
        await init_db()
        self.context = {"tasks": {}}
        evaluator = ConditionEvaluator(self.context)
        
        async with AsyncSessionLocal() as session:
            db_exec = WorkflowExecution(
                workflow_name=workflow.name,
                status="running",
                start_time=datetime.now(timezone.utc)
            )
            session.add(db_exec)
            await session.commit()
            await session.refresh(db_exec)

            print(f"Starting workflow: {workflow.name} (Execution ID: {db_exec.id})")
            
            try:
                executed_task_ids: Set[str] = set()
                remaining_tasks = list(workflow.tasks)

                while remaining_tasks:
                    # Find tasks whose dependencies are met
                    runnable_tasks = [
                        t for t in remaining_tasks 
                        if all(dep in executed_task_ids for dep in t.depends_on)
                    ]

                    if not runnable_tasks and remaining_tasks:
                        raise Exception("Circular dependency detected or missing dependency in workflow.")

                    # Execute runnable tasks in parallel
                    async def run_task_wrapper(task):
                        # Use a separate session for each parallel task to avoid session conflicts
                        async with AsyncSessionLocal() as task_session:
                            # Evaluate condition before execution
                            if not evaluator.evaluate(task.when):
                                print(f"Skipping task: {task.name} (ID: {task.id}) - condition '{task.when}' not met.")
                                await self._record_skipped_task(task, db_exec.id, task_session)
                                return task.id, "SKIPPED"

                            result = await self.execute_task_in_context(task, db_exec.id, task_session)
                            return task.id, result

                    task_results = await asyncio.gather(*(run_task_wrapper(t) for t in runnable_tasks))

                    for task_id, result in task_results:
                        # Store in context for variable passing
                        outputs = {}
                        if result == "SKIPPED":
                             outputs = {} # No outputs for skipped tasks
                        elif isinstance(result, TaskResult):
                            outputs = result.outputs
                        
                        self.context["tasks"][task_id] = {"outputs": outputs}
                        
                        executed_task_ids.add(task_id)
                        # Find and remove the task object from remaining_tasks
                        task_obj = next(t for t in remaining_tasks if t.id == task_id)
                        remaining_tasks.remove(task_obj)
                
                db_exec.status = "completed"
            except Exception as e:
                db_exec.status = "failed"
                print(f"Workflow stopped due to failure: {e}")
                raise e
            finally:
                db_exec.end_time = datetime.now(timezone.utc)
                await session.commit()
                print(f"Workflow {db_exec.status}: {workflow.name}")

    async def _record_skipped_task(self, task: WorkflowTask, execution_id: str, session: AsyncSession):
        """Records a skipped task in the database."""
        db_task = TaskExecution(
            execution_id=execution_id,
            task_name=task.name,
            adapter=task.adapter,
            status="skipped",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc)
        )
        session.add(db_task)
        await session.commit()

    def _resolve_variables(self, params: Any) -> Any:
        """Recursively resolves {{ tasks.ID.outputs.KEY }} in params."""
        if isinstance(params, str):
            pattern = r"\{\{\s*tasks\.(\w+)\.outputs\.(\w+)\s*\}\}"
            matches = re.findall(pattern, params)
            for task_id, key in matches:
                val = self.context.get("tasks", {}).get(task_id, {}).get("outputs", {}).get(key)
                if val is not None:
                    params = params.replace(f"{{{{ tasks.{task_id}.outputs.{key} }}}}", str(val))
            return params
        elif isinstance(params, dict):
            return {k: self._resolve_variables(v) for k, v in params.items()}
        elif isinstance(params, list):
            return [self._resolve_variables(i) for i in params]
        return params

    async def execute_task_in_context(self, task: WorkflowTask, execution_id: str, session: AsyncSession):
        """Executes a task with retries, timeouts, and variable resolution."""
        # Resolve variables in params
        resolved_params = self._resolve_variables(task.params)

        db_task = TaskExecution(
            execution_id=execution_id,
            task_name=task.name,
            adapter=task.adapter,
            status="running",
            start_time=datetime.now(timezone.utc)
        )
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)

        print(f"Executing task: {task.name} (ID: {task.id}) with adapter: {task.adapter}")
        
        last_error = None
        for attempt in range(task.retries + 1):
            if attempt > 0:
                print(f"Retrying task {task.id} (Attempt {attempt}/{task.retries})...")
            
            try:
                adapter = self.adapters.get(task.adapter)
                # Apply timeout
                result = await asyncio.wait_for(adapter.run(resolved_params), timeout=task.timeout)
                
                db_task.status = "completed"
                db_task.end_time = datetime.now(timezone.utc)
                
                entities = []
                if isinstance(result, TaskResult):
                    entities = result.entities
                    db_task.raw_output = result.raw_output
                    db_task.result_json = {"outputs": result.outputs, "entities": [self._som_to_dict(e) for e in entities]}
                elif isinstance(result, list):
                    entities = result
                    db_task.result_json = [self._som_to_dict(e) for e in entities]
                else:
                    entities = [result]
                    db_task.result_json = [self._som_to_dict(e) for e in entities]

                for item in entities:
                    await self._persist_som_object(item, session)
                    
                await session.commit()
                return result

            except asyncio.TimeoutError:
                last_error = f"Task timed out after {task.timeout}s"
                print(f"Error: {last_error}")
            except Exception as e:
                last_error = str(e)
                print(f"Error executing task: {last_error}")
            
            if attempt < task.retries:
                await asyncio.sleep(2 ** attempt) # Exponential backoff

        # If we reach here, all attempts failed
        db_task.status = "failed"
        db_task.end_time = datetime.now(timezone.utc)
        db_task.error = last_error
        await session.commit()
        raise Exception(f"Task {task.id} failed after {task.retries + 1} attempts: {last_error}")

    def _som_to_dict(self, obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode='json')
        return obj

    async def _persist_som_object(self, obj: Any, session: AsyncSession):
        """Persists a SOM object into the database."""
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
        """Legacy compatibility wrapper."""
        adapter = self.adapters.get(task.adapter)
        return await adapter.run(task.params)
