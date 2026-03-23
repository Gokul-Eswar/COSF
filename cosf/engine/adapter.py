import logging
import docker
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
from cosf.engine.normalization import NormalizationEngine
from cosf.utils.secrets import get_secret_manager

class TaskResult(BaseModel):
    """Encapsulates the result of a task execution."""
    entities: List[Any] = []
    outputs: Dict[str, Any] = {}
    raw_output: Optional[str] = None
    error: Optional[str] = None

class BaseAdapter(ABC):
    """Base class for all security tool adapters.
    
    Provides common utilities for logging, error handling, and Docker management.
    """
    
    ADAPTER_NAME: str = "base"
    ADAPTER_DESCRIPTION: str = "Base adapter"

    def __init__(self):
        self.logger = logging.getLogger(f"cosf.adapter.{self.__class__.__name__}")
        self._docker_client: Optional[docker.DockerClient] = None
        self._secret_manager = get_secret_manager()

    @property
    def docker_client(self) -> docker.DockerClient:
        """Lazily initializes and returns a Docker client."""
        if self._docker_client is None:
            try:
                self._docker_client = docker.from_env()
            except Exception as e:
                self.logger.error(f"Failed to initialize Docker client: {e}")
                raise RuntimeError("Docker is not available or accessible")
        return self._docker_client

    async def run(self, params: Dict[str, Any], dry_run: bool = False) -> Union[TaskResult, List[Any], Dict[str, Any]]:
        """Template method for running an adapter, handling dry-run logic."""
        # Resolve secrets in parameters before execution
        resolved_params = self._resolve_secrets(params)
        
        if dry_run:
            from cosf.engine.simulation import MockResponseGenerator
            self.logger.info(f"Running {self.ADAPTER_NAME} in DRY-RUN mode.")
            return MockResponseGenerator.generate(self.ADAPTER_NAME, resolved_params)
        
        return await self._run(resolved_params)

    def _resolve_secrets(self, params: Any) -> Any:
        """Recursively resolves secret references in the parameters."""
        if isinstance(params, dict):
            return {k: self._resolve_secrets(v) for k, v in params.items()}
        elif isinstance(params, list):
            return [self._resolve_secrets(v) for v in params]
        elif isinstance(params, str) and params.startswith("secret:"):
            # Format: secret:path/to/secret:key
            parts = params.split(":", 2)
            if len(parts) == 3:
                _, path, key = parts
                secret_value = self._secret_manager.get_secret(path, key)
                if secret_value:
                    return secret_value
                else:
                    self.logger.warning(f"Secret not found: {path}:{key}")
            return params
        return params

    @abstractmethod
    async def _run(self, params: Dict[str, Any]) -> Union[TaskResult, List[Any], Dict[str, Any]]:
        """Actual tool execution logic to be implemented by subclasses."""
        pass

    def normalize(self, raw_output: str) -> List[Any]:
        """Automatically normalizes raw tool output using the central engine."""
        return NormalizationEngine.normalize_output(self.ADAPTER_NAME, raw_output)

    def run_container(self, image: str, command: str, **kwargs) -> str:
        """Helper to run a command in a Docker container and return output."""
        self.logger.info(f"Running container {image} with command: {command}")
        try:
            container_output = self.docker_client.containers.run(
                image, command, remove=True, **kwargs
            )
            return container_output.decode("utf-8")
        except Exception as e:
            self.logger.error(f"Container execution failed: {e}")
            raise RuntimeError(f"Failed to execute tool {image}: {e}")

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

    def list_adapters(self) -> Dict[str, BaseAdapter]:
        """Returns all registered adapters."""
        return self._adapters
