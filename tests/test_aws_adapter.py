import pytest
import asyncio
from unittest.mock import MagicMock, patch
from cosf.engine.adapters.aws import AwsAdapter
from cosf.models.som import Asset
from cosf.engine.adapter import TaskResult
from moto import mock_aws
import boto3

@pytest.mark.asyncio
async def test_aws_adapter_s3_list():
    with mock_aws():
        # Setup mock S3
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="public-bucket")
        s3.create_bucket(Bucket="private-bucket")
        
        adapter = AwsAdapter()
        result = await adapter.run({
            "operation": "s3_list_buckets",
            "region": "us-east-1"
        })
        
        assert isinstance(result, TaskResult)
        assert len(result.entities) == 2
        assert "public-bucket" in result.outputs["bucket_names"]
        assert "private-bucket" in result.outputs["bucket_names"]
        
        assets = [e for e in result.entities if isinstance(e, Asset)]
        assert len(assets) == 2
        assert assets[0].name.startswith("s3://")

@pytest.mark.asyncio
async def test_aws_adapter_missing_op():
    adapter = AwsAdapter()
    with pytest.raises(ValueError, match="AwsAdapter requires an 'operation' parameter"):
        await adapter.run({})

@pytest.mark.asyncio
async def test_aws_adapter_unsupported_op():
    adapter = AwsAdapter()
    with pytest.raises(ValueError, match="Unsupported AWS operation: non_existent"):
        await adapter.run({"operation": "non_existent"})
