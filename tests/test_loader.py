import pytest
from unittest.mock import patch, MagicMock
from cosf.engine.loader import load_adapters, list_available_plugins
from cosf.engine.adapter import AdapterRegistry, BaseAdapter

def test_load_adapters_builtin():
    registry = AdapterRegistry()
    # Mocking importlib and pkgutil to simulate finding a module
    with patch("importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_module.__path__ = ["/fake/path"]
        mock_import.return_value = mock_module
        
        with patch("pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = [(None, "nmap", False)]
            
            # Simulate a class in the module
            class FakeAdapter(BaseAdapter):
                ADAPTER_NAME = "fake"
                async def _run(self, params): return {}
            
            with patch("inspect.getmembers") as mock_members:
                mock_members.return_value = [("FakeAdapter", FakeAdapter)]
                
                load_adapters(registry, package_name="cosf.engine.adapters")
                assert "fake" in registry.list_adapters()

def test_list_available_plugins():
    with patch("importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_module.__path__ = ["/fake/path"]
        mock_import.return_value = mock_module
        
        with patch("pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = [(None, "nmap", False)]
            
            class FakeAdapter(BaseAdapter):
                ADAPTER_NAME = "fake"
                async def _run(self, params): return {}
                
            with patch("inspect.getmembers") as mock_members:
                mock_members.return_value = [("FakeAdapter", FakeAdapter)]
                
                plugins = list_available_plugins(package_name="cosf.engine.adapters")
                assert "fake" in plugins
