from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Asset, Service, Vulnerability

class MockAdapter(BaseAdapter):
    """A mock adapter for testing purposes."""
    
    ADAPTER_NAME = "mock"

    async def run(self, params: Dict[str, Any]) -> TaskResult:
        target = params.get("target", "127.0.0.1")
        
        asset = Asset(name=f"mock-{target}", ip_address=target)
        service = Service(asset_id=asset.id, port=80, protocol="tcp", name="http", state="open")
        vuln = Vulnerability(
            asset_id=asset.id, 
            severity="high", 
            description=f"Mock vulnerability on {target}", 
            service_id=service.id
        )
        
        return TaskResult(
            entities=[asset, service, vuln],
            outputs={"target_ip": target, "status": "scanned"},
            raw_output=f"DEBUG: Mock scan results for {target}\nFOUND: Port 80 OPEN\nRESULT: 1 vulnerability detected."
        )
