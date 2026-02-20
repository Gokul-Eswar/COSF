import pytest
from abc import ABC
from cosf.engine.adapter import BaseAdapter, AdapterRegistry

class MockAdapter(BaseAdapter):
    async def run(self, params: dict):
        return {"status": "ok", "params": params}

@pytest.mark.asyncio
async def test_adapter_registration():
    registry = AdapterRegistry()
    adapter = MockAdapter()
    registry.register("mock", adapter)
    
    assert registry.get("mock") == adapter
    with pytest.raises(KeyError, match="Adapter 'non-existent' not found in registry"):
        registry.get("non-existent")

@pytest.mark.asyncio
async def test_base_adapter_is_abstract():
    with pytest.raises(TypeError):
        BaseAdapter()

@pytest.mark.asyncio
async def test_mock_adapter_execution():
    adapter = MockAdapter()
    result = await adapter.run({"test": "data"})
    assert result["status"] == "ok"
    assert result["params"]["test"] == "data"
