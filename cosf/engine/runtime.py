import asyncio
from typing import List, Any, Dict
from cosf.parser.workflow import WorkflowSchema, WorkflowTask
from cosf.engine.adapter import AdapterRegistry

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
        print(f"Starting workflow: {workflow.name}")
        for task in workflow.tasks:
            try:
                await self.execute_task(task)
            except Exception as e:
                print(f"Workflow stopped due to task failure: {task.name}")
                raise e
        print(f"Workflow completed: {workflow.name}")

    async def execute_task(self, task: WorkflowTask) -> Any:
        """Executes a single workflow task using the appropriate adapter.

        Args:
            task: The WorkflowTask to execute.

        Returns:
            The result of the adapter's run method.
        """
        print(f"Executing task: {task.name} with adapter: {task.adapter}")
        adapter = self.adapters.get(task.adapter)
        return await adapter.run(task.params)
