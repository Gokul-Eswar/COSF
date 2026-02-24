import pytest
from typer.testing import CliRunner
from cosf.cli import app
from unittest.mock import patch, MagicMock, AsyncMock
import json

runner = CliRunner()

@patch("cosf.cli.AsyncSessionLocal")
def test_cli_history(mock_session_local):
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session
    
    mock_exec = MagicMock(id="123", workflow_name="Test", status="completed", start_time=MagicMock())
    mock_exec.start_time.strftime.return_value = "2026-01-01"
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_exec]
    mock_session.execute.return_value = mock_result
    
    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    assert "123" in result.output
    assert "Test" in result.output

@patch("cosf.cli.AsyncSessionLocal")
@patch("cosf.engine.reporting.ReportingEngine.generate_report", new_callable=AsyncMock)
def test_cli_report(mock_gen_report, mock_session_local):
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session
    
    mock_exec = MagicMock(id="123")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_exec
    mock_session.execute.return_value = mock_result
    
    mock_gen_report.return_value = "reports/123/report.md"
    
    result = runner.invoke(app, ["report", "123"])
    assert result.exit_code == 0
    assert "Report generated successfully" in result.output

def test_cli_plugins_list():
    with patch("cosf.cli.list_available_plugins") as mock_list:
        mock_list.return_value = {"nmap": "cosf.engine.adapters.nmap.NmapAdapter"}
        result = runner.invoke(app, ["plugins", "list"])
        assert result.exit_code == 0
        assert "nmap" in result.output

@patch("cosf.engine.graph.GraphEngine.build_from_db", new_callable=AsyncMock)
def test_cli_graph_analyze(mock_build):
    result = runner.invoke(app, ["graph", "analyze"])
    assert result.exit_code == 0
    assert "Graph Analysis Summary" in result.output

@patch("cosf.engine.graph.GraphEngine.build_from_db", new_callable=AsyncMock)
def test_cli_graph_visualize(mock_build):
    with patch("cosf.engine.graph.GraphEngine.get_graph_data") as mock_get_data:
        mock_get_data.return_value = {"nodes": [], "links": []}
        result = runner.invoke(app, ["graph", "visualize"])
        assert result.exit_code == 0
        assert '"nodes": []' in result.output

@patch("cosf.ai.engine.GenerativeEngine.generate_workflow", new_callable=AsyncMock)
@patch("cosf.ai.engine.GenerativeEngine.validate_generated_yaml")
def test_cli_generate(mock_validate, mock_generate):
    mock_generate.return_value = "name: AI Workflow
tasks: []"
    result = runner.invoke(app, ["generate", "Scan my network"])
    assert result.exit_code == 0
    assert "AI Workflow" in result.output
    assert "Workflow validation: SUCCESS" in result.output
