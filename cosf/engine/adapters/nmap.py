import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Union
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Asset, Service

class NmapAdapter(BaseAdapter):
    """Adapter for the Nmap security scanner."""
    
    ADAPTER_NAME = "nmap"
    ADAPTER_DESCRIPTION = "Scans targets for open ports and services. Requires 'target' parameter (IP or hostname)."

    async def run(self, params: Dict[str, Any]) -> TaskResult:
        target = params.get("target")
        if not target:
            raise ValueError("Nmap adapter requires a 'target' parameter")

        self.logger.info(f"Running Nmap scan on target: {target}")
        
        # Use helper from BaseAdapter
        xml_output = self.run_container(
            "instrumentisto/nmap",
            f"-oX - {target}"
        )
        
        entities = self._parse_xml(xml_output)
        
        # Capture the first IP found as an output for downstream tasks
        target_ip = target
        if entities and isinstance(entities[0], Asset):
            target_ip = str(entities[0].ip_address)

        return TaskResult(
            entities=entities,
            outputs={"target_ip": target_ip},
            raw_output=xml_output
        )

    def _parse_xml(self, xml_content: str) -> List[Union[Asset, Service]]:
        root = ET.fromstring(xml_content)
        entities = []

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
            entities.append(asset)

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
                    entities.append(service)

        return entities
