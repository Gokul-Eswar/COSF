import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import hvac

class SecretManager(ABC):
    """Base class for managing sensitive credentials."""
    
    @abstractmethod
    def get_secret(self, path: str, key: str) -> Optional[str]:
        """Retrieves a secret value from the store."""
        pass

    @abstractmethod
    def set_secret(self, path: str, key: str, value: str):
        """Stores a secret value in the store."""
        pass

class MockSecretManager(SecretManager):
    """In-memory secret manager for testing and local development."""
    
    def __init__(self):
        self._secrets: Dict[str, Dict[str, str]] = {}

    def get_secret(self, path: str, key: str) -> Optional[str]:
        return self._secrets.get(path, {}).get(key)

    def set_secret(self, path: str, key: str, value: str):
        if path not in self._secrets:
            self._secrets[path] = {}
        self._secrets[path][key] = value

class VaultSecretManager(SecretManager):
    """HashiCorp Vault implementation of the SecretManager."""
    
    def __init__(self, url: str, token: str, mount_point: str = "secret"):
        self.client = hvac.Client(url=url, token=token)
        self.mount_point = mount_point

    def get_secret(self, path: str, key: str) -> Optional[str]:
        try:
            read_response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            return read_response["data"]["data"].get(key)
        except Exception:
            return None

    def set_secret(self, path: str, key: str, value: str):
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                mount_point=self.mount_point,
                secret={key: value}
            )
        except Exception as e:
            raise RuntimeError(f"Failed to set secret in Vault: {e}")

def get_secret_manager() -> SecretManager:
    """Factory function to return the configured SecretManager."""
    vault_url = os.getenv("VAULT_URL")
    vault_token = os.getenv("VAULT_TOKEN")
    
    if vault_url and vault_token:
        return VaultSecretManager(url=vault_url, token=vault_token)
    
    # Fallback to Mock for now, or could use EnvSecretManager
    return MockSecretManager()
