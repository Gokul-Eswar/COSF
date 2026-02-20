import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from cosf.engine.adapters.nmap import NmapAdapter
from cosf.models.som import Asset, Service

@pytest.mark.asyncio
async def test_nmap_adapter_missing_target():
    adapter = NmapAdapter()
    with pytest.raises(ValueError, match="Nmap adapter requires a 'target' parameter"):
        await adapter.run({})
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
    
    # We'll mock the actual docker execution later, for now test parsing logic
    with patch("cosf.engine.adapters.nmap.NmapAdapter._run_nmap", return_value=mock_xml):
        results = await adapter.run({"target": "192.168.1.1"})
        
        assert len(results["assets"]) == 1
        asset = results["assets"][0]
        assert asset.name == "test-host"
        assert str(asset.ip_address) == "192.168.1.1"
        
        assert len(results["services"]) == 2
        assert results["services"][0].port == 80
        assert results["services"][1].port == 443
