import hashlib
from typing import Optional, Dict, Any
from cosf.models.som import Evidence
from cosf.utils.storage import StorageProvider, LocalStorageProvider

class EvidenceManager:
    """Manages the storage and retrieval of binary evidence artifacts."""

    def __init__(self, storage: Optional[StorageProvider] = None):
        self.storage = storage or LocalStorageProvider(storage_path="cosf_evidence")

    def store_artifact(self, name: str, artifact_type: str, data: bytes, task_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> Evidence:
        """Stores a binary artifact and returns an Evidence SOM object."""
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(data).hexdigest()
        
        # Determine unique key/filename
        file_extension = self._get_extension(artifact_type)
        key = f"{sha256_hash}{file_extension}"
        
        # Store using provider
        ref_path = self.storage.store(key, data)
        
        # Create SOM object
        evidence = Evidence(
            name=name,
            type=artifact_type,
            file_path=ref_path,
            hash_sha256=sha256_hash,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        return evidence

    def _get_extension(self, artifact_type: str) -> str:
        mapping = {
            "pcap": ".pcap",
            "screenshot": ".png",
            "log": ".log",
            "binary_artifact": ".bin",
            "json": ".json",
            "xml": ".xml"
        }
        return mapping.get(artifact_type.lower(), ".artifact")

    def get_artifact_data(self, evidence: Evidence) -> bytes:
        """Retrieves the raw artifact data."""
        # Note: In a real S3 scenario, this might need parsing the s3:// URI
        # For local paths, it's straightforward.
        key = evidence.file_path.split("/")[-1] # Simplistic for now
        return self.storage.retrieve(key)
