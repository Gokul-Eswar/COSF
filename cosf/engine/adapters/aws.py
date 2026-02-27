import boto3
from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Asset

class AwsAdapter(BaseAdapter):
    """Adapter for AWS infrastructure security assessment."""
    
    ADAPTER_NAME = "aws"
    ADAPTER_DESCRIPTION = "Performs AWS infrastructure reconnaissance and security checks."

    async def run(self, params: Dict[str, Any], dry_run: bool = False) -> TaskResult:
        operation = params.get("operation")
        region = params.get("region", "us-east-1")
        
        if not operation:
            raise ValueError("AwsAdapter requires an 'operation' parameter (e.g., 's3_list_buckets')")

        self.logger.info(f"Executing AWS operation: {operation} in region: {region}")
        
        # Credentials can come from env or params
        session = boto3.Session(
            aws_access_key_id=params.get("aws_access_key_id"),
            aws_secret_access_key=params.get("aws_secret_access_key"),
            aws_session_token=params.get("aws_session_token"),
            region_name=region
        )

        if operation == "s3_list_buckets":
            return await self._s3_list_buckets(session)
        else:
            raise ValueError(f"Unsupported AWS operation: {operation}")

    async def _s3_list_buckets(self, session: boto3.Session) -> TaskResult:
        s3 = session.client('s3')
        response = s3.list_buckets()
        
        buckets = response.get('Buckets', [])
        entities = []
        outputs = {"bucket_names": [b['Name'] for b in buckets]}
        
        for b in buckets:
            name = b['Name']
            # Map each bucket to an Asset (or CloudResource in future)
            # Using a dummy IP for now to satisfy Asset SOM requirements if strict
            asset = Asset(
                name=f"s3://{name}",
                ip_address="0.0.0.0", # Placeholder for cloud resources
                tags=["aws", "s3", "storage"]
            )
            entities.append(asset)
            
        return TaskResult(
            entities=entities,
            outputs=outputs,
            raw_output=str(response)
        )
