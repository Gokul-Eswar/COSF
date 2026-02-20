import asyncio
from typing import List, Any, Dict
from cosf.parser.workflow import WorkflowSchema, WorkflowTask
from cosf.engine.adapter import AdapterRegistry

class ExecutionEngine:
    def __init__(self, adapter_registry: AdapterRegistry = None):
        self.adapters = adapter_registry or AdapterRegistry()

    async def run(self, workflow: WorkflowSchema):
        print(f"Starting workflow: {workflow.name}")
        for task in workflow.tasks:
            try:
                await self.execute_task(task)
            except Exception as e:
                print(f"Workflow stopped due to task failure: {task.name}")
                raise e
        print(f"Workflow completed: {workflow.name}")

    async def execute_task(self, task: WorkflowTask) -> Any:
        print(f"Executing task: {task.name} with adapter: {task.adapter}")
        adapter = self.adapters.get(task.adapter)
        return await adapter.run(task.params)
