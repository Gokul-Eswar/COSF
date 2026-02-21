import pytest
import yaml
from unittest.mock import patch, MagicMock
from cosf.cli import app
from typer.testing import CliRunner

runner = CliRunner()

@pytest.fixture
def complex_workflow(tmp_path):
    workflow_data = {
        "name": "E2E Assessment",
        "tasks": [
            {
                "name": "Scan Network",
                "adapter": "nmap",
                "params": {"target": "127.0.0.1"}
            },
            {
                "name": "Vulnerability Scan",
                "adapter": "nuclei",
                "params": {"target": "https://127.0.0.1"}
            }
        ]
    }
    workflow_file = tmp_path / "e2e_workflow.yaml"
    with open(workflow_file, "w") as f:
        yaml.dump(workflow_data, f)
    return str(workflow_file)

@patch("docker.from_env")
def test_e2e_workflow_execution(mock_docker_from_env, complex_workflow):
    # Mock Docker client
    mock_client = MagicMock()
    mock_docker_from_env.return_value = mock_client
    
    # Mock Nmap output (XML)
    mock_nmap_container_output = b'<?xml version="1.0"?><nmaprun><host><address addr="127.0.0.1"/><ports><port portid="80" protocol="tcp"><state state="open"/><service name="http"/></port></ports></host></nmaprun>'
    
    # Mock Nuclei output (JSON per line)
    mock_nuclei_container_output = b'{"template-id":"http-exposed-panel","info":{"name":"Exposed Panel","severity":"info"},"ip":"127.0.0.1","matched-at":"http://127.0.0.1"}'
    
    # Set up return values for sequential calls
    mock_client.containers.run.side_effect = [
        mock_nmap_container_output,
        mock_nuclei_container_output
    ]

    # Run CLI
    result = runner.invoke(app, ["run", complex_workflow])
    
    if result.exit_code != 0:
        print(f"CLI Error: {result.output}")

    assert result.exit_code == 0
    assert "Workflow 'E2E Assessment' completed successfully" in result.output
    
    # Verify both adapters were called
    assert mock_client.containers.run.call_count == 2

