import pytest
import os
import shutil
from cosf.utils.storage import LocalStorageProvider, S3StorageProvider
from cosf.models.evidence import EvidenceManager
from moto import mock_aws
import boto3

def test_local_storage_provider():
    storage_path = "test_local_storage"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)
    
    provider = LocalStorageProvider(storage_path=storage_path)
    data = b"hello local world"
    key = "test.txt"
    
    path = provider.store(key, data)
    assert os.path.exists(path)
    assert provider.retrieve(key) == data
    assert provider.exists(key) is True
    
    shutil.rmtree(storage_path)

@mock_aws
def test_s3_storage_provider():
    bucket_name = "test-bucket"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)
    
    provider = S3StorageProvider(bucket=bucket_name)
    data = b"hello s3 world"
    key = "evidence/test.bin"
    
    ref = provider.store(key, data)
    assert ref == f"s3://{bucket_name}/{key}"
    assert provider.retrieve(key) == data
    assert provider.exists(key) is True

@mock_aws
def test_evidence_manager_with_s3():
    bucket_name = "evidence-bucket"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)
    
    s3_provider = S3StorageProvider(bucket=bucket_name)
    manager = EvidenceManager(storage=s3_provider)
    
    data = b"artifact data"
    evidence = manager.store_artifact(
        name="cloud_log",
        artifact_type="log",
        data=data,
        task_id="task-cloud-1"
    )
    
    assert evidence.file_path.startswith("s3://")
    assert manager.get_artifact_data(evidence) == data
