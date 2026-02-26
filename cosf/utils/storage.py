from abc import ABC, abstractmethod
from typing import Optional
import os
import shutil

class StorageProvider(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def store(self, key: str, data: bytes) -> str:
        """Stores data and returns a reference or path."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> bytes:
        """Retrieves data by key."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Checks if a key exists."""
        pass

class LocalStorageProvider(StorageProvider):
    """Stores data on the local filesystem."""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def store(self, key: str, data: bytes) -> str:
        dest_path = os.path.join(self.storage_path, key)
        # Ensure subdirectories exist if key contains slashes
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return dest_path

    def retrieve(self, key: str) -> bytes:
        path = os.path.join(self.storage_path, key)
        with open(path, "rb") as f:
            return f.read()

    def exists(self, key: str) -> bool:
        return os.path.exists(os.path.join(self.storage_path, key))

class S3StorageProvider(StorageProvider):
    """Stores data in an S3-compatible bucket."""
    
    def __init__(self, bucket: str, endpoint_url: Optional[str] = None, 
                 access_key: Optional[str] = None, secret_key: Optional[str] = None):
        import boto3
        from botocore.config import Config
        
        self.bucket = bucket
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4')
        )
        # Ensure bucket exists (optional, could fail if no permissions)
        # self.s3.create_bucket(Bucket=bucket)

    def store(self, key: str, data: bytes) -> str:
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"

    def retrieve(self, key: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()

    def exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False
