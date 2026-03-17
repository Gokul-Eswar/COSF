import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from cosf.engine.adapters.shodan import ShodanAdapter
from cosf.engine.adapter import TaskResult
from cosf.models.som import Asset, Service

@pytest.mark.asyncio
async def test_shodan_adapter_run():
    adapter = ShodanAdapter()
    params = {"query": "apache", "api_key": "test-key"}
    
    mock_data = {
        "total": 1,
        "matches": [
            {
                "ip_str": "1.1.1.1",
                "hostnames": ["test.com"],
                "port": 80,
                "product": "Apache",
                "version": "2.4.41"
            }
        ]
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mock_response.text = json.dumps(mock_data)
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await adapter.run(params)
        
    assert isinstance(result, TaskResult)
    assert result.outputs["total"] == 1
    assert len(result.entities) == 2 # 1 Asset + 1 Service
    
    asset = next(e for e in result.entities if isinstance(e, Asset))
    assert str(asset.ip_address) == "1.1.1.1"
    assert asset.name == "test.com"
    
    service = next(e for e in result.entities if isinstance(e, Service))
    assert service.port == 80
    assert service.product == "Apache"

@pytest.mark.asyncio
async def test_shodan_adapter_missing_params():
    adapter = ShodanAdapter()
    
    with pytest.raises(ValueError, match="requires an 'api_key'"):
        await adapter.run({"query": "apache"})
        
    with pytest.raises(ValueError, match="requires a 'query'"):
        await adapter.run({"api_key": "key"})

@pytest.mark.asyncio
async def test_shodan_adapter_api_error():
    adapter = ShodanAdapter()
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Invalid API key"}
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Shodan API failed: Invalid API key"):
            await adapter.run({"query": "a", "api_key": "b"})
