import httpx
import asyncio
from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Vulnerability

class BurpAdapter(BaseAdapter):
    """Adapter for Burp Suite Enterprise/Professional REST API."""
    
    ADAPTER_NAME = "burp"
    ADAPTER_DESCRIPTION = "Initiates and retrieves results from Burp Suite Professional/Enterprise scans."

    async def run(self, params: Dict[str, Any]) -> TaskResult:
        api_url = params.get("api_url", "http://127.0.0.1:1337")
        api_key = params.get("api_key")
        target = params.get("target") # URL to scan
        
        if not target:
             raise ValueError("Burp adapter requires a 'target' URL.")

        self.logger.info(f"Initiating Burp scan for: {target}")

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            try:
                # 1. Start scan (POST /v0.1/scan)
                # Note: Burp REST API structure can vary by version, using common patterns
                response = await client.post(
                    f"{api_url}/v0.1/scan",
                    json={"urls": [target]}
                )
                response.raise_for_status()
                
                # Usually returns scan ID in Location header or body
                scan_location = response.headers.get("Location")
                if not scan_location:
                    # Try to parse from JSON body
                    scan_id = response.json().get("scan_id")
                    scan_location = f"/v0.1/scan/{scan_id}"
                
                self.logger.info(f"Burp scan initiated: {scan_location}")
                
                # In a real workflow, we might poll for completion.
                # For the adapter, we return the scan info.
                
                return TaskResult(
                    entities=[], # Results would be fetched later or by a separate task
                    outputs={"scan_location": scan_location},
                    raw_output=response.text
                )
                
            except Exception as e:
                self.logger.error(f"Burp API request failed: {e}")
                raise RuntimeError(f"Burp error: {e}")
