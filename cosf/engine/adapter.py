from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    @abstractmethod
    async def run(self, params: Dict[str, Any]) -> Any:
        """Execute the adapter's task with provided parameters."""
        return params

class AdapterRegistry:
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}

    def register(self, name: str, adapter: BaseAdapter):
        self._adapters[name] = adapter

    def get(self, name: str) -> BaseAdapter:
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' not found in registry")
        return self._adapters[name]
