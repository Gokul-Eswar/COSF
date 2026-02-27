from unittest.mock import patch
import pytest
from typer.testing import CliRunner
import yaml
from cosf.cli import app

runner = CliRunner()

@pytest.fixture
def sample_workflow(tmp_path):
    workflow_data = {
        "name": "Test Workflow",
        "tasks": [
            {
                "name": "Task 1",
                "adapter": "nmap",
                "params": {"target": "127.0.0.1"}
            }
        ]
    }
    workflow_file = tmp_path / "workflow.yaml"
    with open(workflow_file, "w") as f:
        yaml.dump(workflow_data, f)
    return str(workflow_file)

def test_cli_run_executes_workflow(sample_workflow):
    # Mock the engine's run method to avoid actual execution
    with patch("cosf.engine.runtime.ExecutionEngine.run", return_value=None) as mock_run:
        result = runner.invoke(app, ["run", sample_workflow], catch_exceptions=False)
    
    assert result.exit_code == 0
    assert "Workflow 'Test Workflow' completed successfully" in result.output
    assert mock_run.called

def test_cli_run_fails_with_invalid_file():
    # If catch_exceptions is False, runner will raise exceptions instead of returning result.exit_code != 0 if it's not a SystemExit
    # But Typer.Exit(code=1) *is* a SystemExit.
    result = runner.invoke(app, ["run", "non_existent_file.yaml"], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Error: File 'non_existent_file.yaml' not found" in result.output

def test_cli_run_fails_with_invalid_yaml(tmp_path):
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("invalid: [yaml: content")
    
    result = runner.invoke(app, ["run", str(invalid_file)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "Error: Failed to parse YAML" in result.output
