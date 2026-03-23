import asyncio
from cosf.parser.workflow import WorkflowParser
from cosf.engine.runtime import ExecutionEngine
from cosf.engine.adapter import AdapterRegistry
from cosf.engine.loader import load_adapters

def get_engine():
    """Initializes and returns an ExecutionEngine with dynamically loaded adapters."""
    registry = AdapterRegistry()
    load_adapters(registry)
    return ExecutionEngine(adapter_registry=registry)

async def run_workflow_task(execution_id: str, workflow_yaml: str, dry_run: bool = False):
    """Asynchronous entry point for workflow execution."""
    parser = WorkflowParser()
    workflow = parser.parse(workflow_yaml)
    engine = get_engine()
    await engine.run(workflow, dry_run=dry_run)

def sync_run_workflow_task(execution_id: str, workflow_yaml: str, dry_run: bool = False):
    """Synchronous wrapper for RQ workers to execute asynchronous workflows."""
    asyncio.run(run_workflow_task(execution_id, workflow_yaml, dry_run))
