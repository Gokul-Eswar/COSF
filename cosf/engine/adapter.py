from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    @abstractmethod
    async def run(self, params: Dict[str, Any]) -> Any:
        """Execute the adapter's task with provided parameters."""
        return params

class AdapterRegistry:
    """A registry for managing and retrieving tool adapters.

    This class provides a central registration point for various security tool
    adapters, allowing the engine to dynamically retrieve them by name.
    """

    def __init__(self):
        """Initializes an empty adapter registry."""
        self._adapters: Dict[str, BaseAdapter] = {}

    def register(self, name: str, adapter: BaseAdapter):
        """Registers a new adapter with the given name.

        Args:
            name: The unique identifier for the adapter (e.g., 'nmap').
            adapter: An instance of a class implementing BaseAdapter.
        """
        self._adapters[name] = adapter

    def get(self, name: str) -> BaseAdapter:
        """Retrieves a registered adapter by name.

        Args:
            name: The name of the adapter to retrieve.

        Returns:
            The registered BaseAdapter instance.

        Raises:
            KeyError: If no adapter is registered with the given name.
        """
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' not found in registry")
        return self._adapters[name]
