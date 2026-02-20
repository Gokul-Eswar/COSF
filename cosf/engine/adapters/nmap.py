import xml.etree.ElementTree as ET
from typing import Dict, Any, List
import docker
from cosf.engine.adapter import BaseAdapter
from cosf.models.som import Asset, Service

class NmapAdapter(BaseAdapter):
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None # Fallback for environments without docker

    async def run(self, params: Dict[str, Any]) -> Dict[str, List[Any]]:
        target = params.get("target")
        if not target:
            raise ValueError("Nmap adapter requires a 'target' parameter")

        xml_output = await self._run_nmap(target)
        return self._parse_xml(xml_output)

    async def _run_nmap(self, target: str) -> str:
        if not self.client:
             raise RuntimeError("Docker is not available.")

        # In a real async environment, we would use a thread pool or aiohttp for docker calls
        # For MVP, we'll keep it simple
        container = self.client.containers.run(
            "instrumentisto/nmap",
            f"-oX - {target}",
            remove=True
        )
        return container.decode("utf-8")

    def _parse_xml(self, xml_content: str) -> Dict[str, List[Any]]:
        root = ET.fromstring(xml_content)
        assets = []
        services = []

        for host in root.findall("host"):
            ip_address_elem = host.find("address")
            if ip_address_elem is None:
                continue
            ip_address = ip_address_elem.get("addr")
            
            # Extract hostname if available
            hostname = None
            hostnames_elem = host.find("hostnames")
            if hostnames_elem is not None:
                h_elem = hostnames_elem.find("hostname")
                if h_elem is not None:
                    hostname = h_elem.get("name")
            
            asset = Asset(
                name=hostname or ip_address,
                ip_address=ip_address
            )
            assets.append(asset)

            # Extract ports/services
            ports_elem = host.find("ports")
            if ports_elem is not None:
                for port in ports_elem.findall("port"):
                    port_id = int(port.get("portid"))
                    protocol = port.get("protocol")
                    
                    state_elem = port.find("state")
                    state = state_elem.get("state") if state_elem is not None else None
                    
                    service_elem = port.find("service")
                    service_name = service_elem.get("name") if service_elem is not None else None
                    
                    service = Service(
                        asset_id=asset.id,
                        port=port_id,
                        protocol=protocol,
                        name=service_name,
                        state=state
                    )
                    services.append(service)

        return {"assets": assets, "services": services}
