from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter
from cosf.models.som import Asset, Service, Vulnerability

class MockAdapter(BaseAdapter):
    async def run(self, params: Dict[str, Any]) -> List[Any]:
        target = params.get("target", "127.0.0.1")
        
        asset = Asset(name=f"mock-{target}", ip_address=target)
        service = Service(asset_id=asset.id, port=80, protocol="tcp", name="http", state="open")
        vuln = Vulnerability(
            asset_id=asset.id, 
            severity="high", 
            description="Mock vulnerability", 
            service_id=service.id
        )
        
        return [asset, service, vuln]
