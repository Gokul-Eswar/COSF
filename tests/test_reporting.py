import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from cosf.engine.reporting import ReportingEngine
from cosf.models.database import WorkflowExecution, TaskExecution
from datetime import datetime, timezone

@pytest.fixture
def mock_execution():
    exec_id = "test-exec-id"
    task1 = TaskExecution(
        task_name="Task 1",
        adapter="nmap",
        status="completed",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        raw_output="<nmap>test</nmap>",
        result_json={"entities": []}
    )
    task2 = TaskExecution(
        task_name="Task 2",
        adapter="nuclei",
        status="failed",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        error="Test error"
    )
    
    execution = WorkflowExecution(
        id=exec_id,
        workflow_name="Test Workflow",
        status="completed",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        tasks=[task1, task2]
    )
    # Link back manually for the mock
    task1.execution = execution
    task2.execution = execution
    return execution

@pytest.mark.asyncio
async def test_reporting_engine_markdown(mock_execution, tmp_path):
    report_dir = tmp_path / "reports"
    engine = ReportingEngine(output_base_dir=str(report_dir))
    
    report_path = await engine.generate_report(mock_execution, format="markdown")
    
    assert os.path.exists(report_path)
    content = Path(report_path).read_text()
    assert "# Security Assessment Report: Test Workflow" in content
    assert "Task 1" in content
    assert "Task 2" in content
    assert "evidence/task_1_nmap.xml" in content

@pytest.mark.asyncio
async def test_reporting_engine_json(mock_execution, tmp_path):
    report_dir = tmp_path / "reports"
    engine = ReportingEngine(output_base_dir=str(report_dir))
    
    report_path = await engine.generate_report(mock_execution, format="json")
    
    assert os.path.exists(report_path)
    with open(report_path) as f:
        data = json.load(f)
    assert data["workflow_name"] == "Test Workflow"
    assert len(data["tasks"]) == 2

@pytest.mark.asyncio
async def test_reporting_engine_html(mock_execution, tmp_path):
    report_dir = tmp_path / "reports"
    engine = ReportingEngine(output_base_dir=str(report_dir))
    
    report_path = await engine.generate_report(mock_execution, format="html")
    
    assert os.path.exists(report_path)
    content = Path(report_path).read_text()
    assert "<title>COSF Dashboard - Test Workflow</title>" in content
    assert "Task 1" in content
