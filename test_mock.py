import pytest
import importlib
import pkgutil
import inspect
from unittest.mock import patch, MagicMock
from cosf.engine.loader import load_adapters
from cosf.engine.adapter import AdapterRegistry, BaseAdapter

def test_debug():
    registry = AdapterRegistry()
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
                
                try:
                    package = importlib.import_module("cosf.engine.adapters")
                    print("Package path:", package.__path__)
                    print("Iter modules returns:", pkgutil.iter_modules(package.__path__))
                    for item in pkgutil.iter_modules(package.__path__):
                        print("Item:", item)
                except Exception as e:
                    print("Error:", e)
                

if __name__ == '__main__':
    test_debug()
