import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from cosf.engine.runtime import ExecutionEngine
from cosf.engine.adapter import BaseAdapter, AdapterRegistry
from cosf.parser.workflow import WorkflowSchema, WorkflowTask

class MockAdapter(BaseAdapter):
    async def run(self, params: dict):
        return {"result": "success"}

@pytest.fixture
def engine():
    registry = AdapterRegistry()
    registry.register("mock", MockAdapter())
    return ExecutionEngine(adapter_registry=registry)

@pytest.mark.asyncio
async def test_engine_executes_tasks_sequentially(engine):
    task1 = WorkflowTask(name="Task 1", adapter="mock", params={"p1": "v1"})
    task2 = WorkflowTask(name="Task 2", adapter="mock", params={"p2": "v2"})
    workflow = WorkflowSchema(name="Test Workflow", tasks=[task1, task2])

    # Spy on adapter
    adapter = engine.adapters.get("mock")
    adapter.run = AsyncMock(return_value={"result": "success"})
    
    await engine.run(workflow)
    
    assert adapter.run.call_count == 2
    adapter.run.assert_any_call(task1.params)
    adapter.run.assert_any_call(task2.params)

@pytest.mark.asyncio
async def test_engine_stops_on_failure(engine):
    task1 = WorkflowTask(name="Task 1", adapter="mock", params={})
    task2 = WorkflowTask(name="Task 2", adapter="mock", params={})
    workflow = WorkflowSchema(name="Test Workflow", tasks=[task1, task2])

    # Spy on adapter and fail
    adapter = engine.adapters.get("mock")
    adapter.run = AsyncMock(side_effect=[Exception("Task 1 failed"), {"result": "success"}])
    
    with pytest.raises(Exception, match="Task 1 failed"):
        await engine.run(workflow)
    
    assert adapter.run.call_count == 1

@pytest.mark.asyncio
async def test_engine_executes_task_directly(engine):
    task = WorkflowTask(name="Single Task", adapter="mock", params={})
    result = await engine.execute_task(task)
    assert result == {"result": "success"}
