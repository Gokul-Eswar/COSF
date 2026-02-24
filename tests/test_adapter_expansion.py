import pytest
import json
from unittest.mock import MagicMock, patch
from cosf.engine.adapters.zap import ZapAdapter
from cosf.engine.adapters.python import PythonAdapter
from cosf.engine.adapter import TaskResult

@pytest.mark.asyncio
@patch("cosf.engine.adapter.BaseAdapter.run_container")
async def test_zap_adapter_parsing(mock_run_container):
    # Mock ZAP JSON report
    mock_json = {
        "site": [
            {
                "@host": "127.0.0.1",
                "alerts": [
                    {
                        "pluginid": "1001",
                        "riskdesc": "High (Some confidence)",
                        "name": "XSS",
                        "desc": "Cross-site scripting"
                    }
                ]
            }
        ]
    }
    mock_run_container.return_value = json.dumps(mock_json)
    
    adapter = ZapAdapter()
    result = await adapter.run({"target": "http://127.0.0.1"})
    
    assert len(result.entities) == 1
    vuln = result.entities[0]
    assert vuln.severity == "high"
    assert vuln.cve_id == "1001"

@pytest.mark.asyncio
@patch("cosf.engine.adapter.BaseAdapter.run_container")
async def test_python_adapter_execution(mock_run_container):
    # Mock script output
    mock_output = {"outputs": {"custom_val": 42}, "entities": []}
    mock_run_container.return_value = json.dumps(mock_output)
    
    adapter = PythonAdapter()
    result = await adapter.run({"script": "print('hello')", "base64": False})
    
    assert result.outputs["custom_val"] == 42
    assert isinstance(result, TaskResult)
