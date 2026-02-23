import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from cosf.engine.adapters.nmap import NmapAdapter
from cosf.models.som import Asset, Service
from cosf.engine.adapter import TaskResult

@pytest.mark.asyncio
async def test_nmap_adapter_missing_target():
    adapter = NmapAdapter()
    with pytest.raises(ValueError, match="Nmap adapter requires a 'target' parameter"):
        await adapter.run({})

@pytest.mark.asyncio
async def test_nmap_adapter_execution():
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun>
<host><address addr="192.168.1.1" addrtype="ipv4"/>
<hostnames><hostname name="test-host" type="user"/></hostnames>
<ports>
<port protocol="tcp" portid="80"><state state="open" reason="syn-ack" reason_ttl="0"/><service name="http" method="table" conf="3"/></port>
<port protocol="tcp" portid="443"><state state="open" reason="syn-ack" reason_ttl="0"/><service name="https" method="table" conf="3"/></port>
</ports>
</host>
</nmaprun>
"""
    adapter = NmapAdapter()
    
    # Mock BaseAdapter.run_container instead of internal _run_nmap
    with patch("cosf.engine.adapter.BaseAdapter.run_container", return_value=mock_xml):
        result = await adapter.run({"target": "192.168.1.1"})
        
        assert isinstance(result, TaskResult)
        entities = result.entities
        
        assets = [e for e in entities if isinstance(e, Asset)]
        services = [e for e in entities if isinstance(e, Service)]

        assert len(assets) == 1
        asset = assets[0]
        assert asset.name == "test-host"
        assert str(asset.ip_address) == "192.168.1.1"
        
        assert len(services) == 2
        assert services[0].port == 80
        assert services[1].port == 443
        
        # Verify outputs
        assert result.outputs["target_ip"] == "192.168.1.1"
