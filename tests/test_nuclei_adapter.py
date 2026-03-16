import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from cosf.engine.adapters.nuclei import NucleiAdapter
from cosf.models.som import Vulnerability
from cosf.engine.adapter import TaskResult

@pytest.mark.asyncio
async def test_nuclei_adapter_parsing():
    # Mock Nuclei JSON output (single line per finding)
    mock_output = json.dumps({
        "template-id": "cve-2021-1234",
        "info": {"name": "Test Vulnerability", "severity": "high"},
        "type": "http",
        "host": "http://192.168.1.1",
        "ip": "192.168.1.1",
        "matched-at": "http://192.168.1.1/login",
        "description": "A test vulnerability description"
    })
    
    adapter = NucleiAdapter()
    
    with patch("cosf.engine.adapter.BaseAdapter.run_container", return_value=mock_output):
        result = await adapter.run({"target": "192.168.1.1"})
        
        assert isinstance(result, TaskResult)
        vulnerabilities = result.entities
        
        assert len(vulnerabilities) == 2
        vuln = next(e for e in vulnerabilities if isinstance(e, Vulnerability))
        assert vuln.cve_id == "cve-2021-1234"
        assert vuln.severity == "High"
        assert "Test Vulnerability" in vuln.description

@pytest.mark.asyncio
async def test_nuclei_adapter_missing_target():
    adapter = NucleiAdapter()
    with pytest.raises(ValueError, match="Nuclei adapter requires a 'target' parameter"):
        await adapter.run({})
