import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from cosf.engine.runtime import ExecutionEngine, ConditionEvaluator
from cosf.parser.workflow import WorkflowSchema, WorkflowTask
from cosf.engine.adapter import AdapterRegistry, TaskResult

@pytest.mark.parametrize("condition,context,expected", [
    (None, {}, True),
    ("True", {}, True),
    ("False", {}, False),
    ("1 == 1", {}, True),
    ("1 == 2", {}, False),
    ("'open' == 'open'", {}, True),
    ("'open' != 'closed'", {}, True),
    ("{{ tasks.scan.outputs.status }} == 'open'", {"tasks": {"scan": {"outputs": {"status": "open"}}}}, True),
    ("{{ tasks.scan.outputs.status }} == 'closed'", {"tasks": {"scan": {"outputs": {"status": "open"}}}}, False),
    ("'80' in '80, 443, 8080'", {}, True),
    ("'22' in '80, 443'", {}, False),
    ("'admin' contains 'administrator'", {}, False),
    ("'administrator' contains 'admin'", {}, True),
])
def test_condition_evaluator(condition, context, expected):
    evaluator = ConditionEvaluator(context)
    assert evaluator.evaluate(condition) == expected

@pytest.mark.asyncio
@patch("cosf.engine.runtime.init_db", return_value=None)
@patch("cosf.engine.runtime.AsyncSessionLocal")
async def test_execution_engine_skipping(mock_session_local, mock_init_db):
    # Setup mocks
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session
    
    # Mock engine's DB persisting methods to avoid model issues in mock
    with patch.object(ExecutionEngine, "_persist_som_object", new_callable=AsyncMock):
        registry = AdapterRegistry()
        mock_adapter = MagicMock()
        
        # Task 1 result
        task1_result = TaskResult(outputs={"status": "closed"})
        mock_adapter.run = AsyncMock(return_value=task1_result)
        registry.register("mock", mock_adapter)
        
        engine = ExecutionEngine(adapter_registry=registry)
        
        workflow = WorkflowSchema(
            name="Skipping Workflow",
            tasks=[
                WorkflowTask(id="task1", name="Task 1", adapter="mock"),
                WorkflowTask(
                    id="task2", 
                    name="Task 2", 
                    adapter="mock", 
                    depends_on=["task1"],
                    when="{{ tasks.task1.outputs.status }} == 'open'"
                )
            ]
        )
        
        await engine.run(workflow)
        
        # Task 1 should have run once
        assert mock_adapter.run.call_count == 1
        # Task 2 should NOT have run because status was 'closed'
        assert engine.context["tasks"]["task2"]["outputs"] == {}
        
        # Verify status in context
        assert "task2" in engine.context["tasks"]
        
        # Verify session commit was called (initial exec, task 1 start, task 1 end, task 2 skip, final exec end)
        assert mock_session.commit.call_count >= 3
