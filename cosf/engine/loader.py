import importlib
import inspect
import pkgutil
import sys
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points
from typing import Dict, Type
from cosf.engine.adapter import BaseAdapter, AdapterRegistry

def load_adapters(registry: AdapterRegistry, package_name: str = "cosf.engine.adapters"):
    """Dynamically loads and registers all adapters found in the given package and entry points."""
    # 1. Load from built-in package
    try:
        package = importlib.import_module(package_name)
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                continue
                
            full_module_name = f"{package_name}.{name}"
            module = importlib.import_module(full_module_name)
            
            for class_name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseAdapter) and cls is not BaseAdapter:
                    adapter_name = getattr(cls, "ADAPTER_NAME", name.lower())
                    registry.register(adapter_name, cls())
    except ImportError:
        pass # Built-in package might not exist in some distributions

    # 2. Load from entry points
    eps = entry_points(group='cosf.adapters')
    for entry_point in eps:
        cls = entry_point.load()
        if issubclass(cls, BaseAdapter) and cls is not BaseAdapter:
            adapter_name = getattr(cls, "ADAPTER_NAME", entry_point.name)
            registry.register(adapter_name, cls())

def list_available_plugins(package_name: str = "cosf.engine.adapters") -> Dict[str, str]:
    """Lists all available adapter plugins without registering them."""
    plugins = {}
    
    # 1. List from built-in package
    try:
        package = importlib.import_module(package_name)
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                continue
            
            full_module_name = f"{package_name}.{name}"
            try:
                module = importlib.import_module(full_module_name)
                for class_name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, BaseAdapter) and cls is not BaseAdapter:
                        adapter_name = getattr(cls, "ADAPTER_NAME", name.lower())
                        plugins[adapter_name] = f"{full_module_name}.{class_name}"
            except Exception:
                continue
    except ImportError:
        pass

    # 2. List from entry points
    eps = entry_points(group='cosf.adapters')
    for entry_point in eps:
        plugins[entry_point.name] = f"{entry_point.value} (entry point)"
        
    return plugins
