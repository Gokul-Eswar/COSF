import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from cosf.engine.adapters.nuclei import NucleiAdapter
from cosf.models.som import Vulnerability

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
    
    with patch("cosf.engine.adapters.nuclei.NucleiAdapter._run_nuclei", return_value=mock_output):
        results = await adapter.run({"target": "192.168.1.1"})
        
        assert len(results["vulnerabilities"]) == 1
        vuln = results["vulnerabilities"][0]
        assert vuln.cve_id == "cve-2021-1234"
        assert vuln.severity == "high"
        assert "Test Vulnerability" in vuln.description

@pytest.mark.asyncio
async def test_nuclei_adapter_missing_target():
    adapter = NucleiAdapter()
    with pytest.raises(ValueError, match="Nuclei adapter requires a 'target' parameter"):
        await adapter.run({})
