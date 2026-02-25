import os
import shutil
import hashlib
from typing import Optional, Dict, Any
from cosf.models.som import Evidence

class EvidenceManager:
    """Manages the storage and retrieval of binary evidence artifacts."""

    def __init__(self, storage_path: str = "cosf_evidence"):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def store_artifact(self, name: str, artifact_type: str, data: bytes, task_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> Evidence:
        """Stores a binary artifact and returns an Evidence SOM object."""
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(data).hexdigest()
        
        # Determine file path (use hash for deduplication or unique naming)
        file_extension = self._get_extension(artifact_type)
        filename = f"{sha256_hash}{file_extension}"
        dest_path = os.path.join(self.storage_path, filename)
        
        # Write file if it doesn't exist
        if not os.path.exists(dest_path):
            with open(dest_path, "wb") as f:
                f.write(data)
        
        # Create SOM object
        evidence = Evidence(
            name=name,
            type=artifact_type,
            file_path=dest_path,
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

    def get_artifact_path(self, evidence: Evidence) -> str:
        """Returns the absolute path to the artifact."""
        return os.path.abspath(evidence.file_path)
