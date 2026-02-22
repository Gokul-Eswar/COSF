import importlib
import inspect
import pkgutil
from typing import Dict, Type
from cosf.engine.adapter import BaseAdapter, AdapterRegistry

def load_adapters(registry: AdapterRegistry, package_name: str = "cosf.engine.adapters"):
    """Dynamically loads and registers all adapters found in the given package."""
    package = importlib.import_module(package_name)
    
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
        if is_pkg:
            continue
            
        full_module_name = f"{package_name}.{name}"
        module = importlib.import_module(full_module_name)
        
        for class_name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, BaseAdapter) and cls is not BaseAdapter:
                # Use class name as lowercase as a heuristic for adapter name
                # or look for a special attribute
                adapter_name = getattr(cls, "ADAPTER_NAME", name.lower())
                registry.register(adapter_name, cls())

def list_available_plugins(package_name: str = "cosf.engine.adapters") -> Dict[str, str]:
    """Lists all available adapter plugins without registering them."""
    plugins = {}
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
    return plugins
