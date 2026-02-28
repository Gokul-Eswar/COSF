import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Union
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Asset, Service

class NmapAdapter(BaseAdapter):
    """Adapter for the Nmap security scanner."""
    
    ADAPTER_NAME = "nmap"
    ADAPTER_DESCRIPTION = "Scans targets for open ports and services. Requires 'target' parameter (IP or hostname)."

    async def _run(self, params: Dict[str, Any]) -> TaskResult:
        target = params.get("target")
        if not target:
            raise ValueError("Nmap adapter requires a 'target' parameter")

        self.logger.info(f"Running Nmap scan on target: {target}")
        
        # Use helper from BaseAdapter
        xml_output = self.run_container(
            "instrumentisto/nmap",
            f"-oX - {target}"
        )
        
        entities = self.normalize(xml_output)
        
        # Capture the first IP found as an output for downstream tasks
        target_ip = target
        for e in entities:
            if isinstance(e, Asset):
                target_ip = str(e.ip_address)
                break

        return TaskResult(
            entities=entities,
            outputs={"target_ip": target_ip},
            raw_output=xml_output
        )
