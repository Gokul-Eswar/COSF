import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from cosf.engine.runtime import ExecutionEngine
from cosf.parser.workflow import WorkflowSchema, WorkflowTask

@pytest.mark.asyncio
async def test_engine_executes_tasks_sequentially():
    task1 = WorkflowTask(name="Task 1", adapter="mock", params={"p1": "v1"})
    task2 = WorkflowTask(name="Task 2", adapter="mock", params={"p2": "v2"})
    workflow = WorkflowSchema(name="Test Workflow", tasks=[task1, task2])

    engine = ExecutionEngine()
    
    # Mock adapter execution
    engine.execute_task = AsyncMock(return_value={"result": "success"})
    
    await engine.run(workflow)
    
    assert engine.execute_task.call_count == 2
    engine.execute_task.assert_any_call(task1)
    engine.execute_task.assert_any_call(task2)

@pytest.mark.asyncio
async def test_engine_stops_on_failure():
    task1 = WorkflowTask(name="Task 1", adapter="mock", params={})
    task2 = WorkflowTask(name="Task 2", adapter="mock", params={})
    workflow = WorkflowSchema(name="Test Workflow", tasks=[task1, task2])

    engine = ExecutionEngine()
    
    # Mock adapter failure
    engine.execute_task = AsyncMock(side_effect=[Exception("Task 1 failed"), {"result": "success"}])
    
    with pytest.raises(Exception, match="Task 1 failed"):
        await engine.run(workflow)
    
    assert engine.execute_task.call_count == 1

@pytest.mark.asyncio
async def test_engine_executes_task_directly():
    task = WorkflowTask(name="Single Task", adapter="mock", params={})
    engine = ExecutionEngine()
    result = await engine.execute_task(task)
    assert result == {"result": "success"}
