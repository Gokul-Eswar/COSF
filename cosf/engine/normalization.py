from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
import xml.etree.ElementTree as ET
import json
from cosf.models.som import Asset, Service, Vulnerability, SOMBase

class SeverityMapper:
    """Unifies severity levels across different security tools."""
    
    MAPPING = {
        # Nuclei / Common
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "info": "Info",
        "unknown": "Unknown",
        # Nmap / Others
        "fatal": "Critical",
        "error": "High",
        "warning": "Medium",
        "note": "Low"
    }

    @classmethod
    def normalize(cls, severity: str) -> str:
        return cls.MAPPING.get(severity.lower(), "Unknown")

class BaseNormalizer(ABC):
    """Base class for all tool-specific normalizers."""
    
    @abstractmethod
    def normalize(self, raw_output: str) -> List[SOMBase]:
        pass

class NmapNormalizer(BaseNormalizer):
    """Normalizes Nmap XML output into Asset and Service entities."""
    
    def normalize(self, raw_output: str) -> List[SOMBase]:
        if not raw_output or not raw_output.strip().startswith("<?xml"):
            return []
            
        try:
            root = ET.fromstring(raw_output)
        except Exception:
            return []

        entities = []
        for host in root.findall("host"):
            ip_address_elem = host.find("address")
            if ip_address_elem is None: continue
            ip_address = ip_address_elem.get("addr")
            
            hostname = None
            hostnames_elem = host.find("hostnames")
            if hostnames_elem is not None:
                h_elem = hostnames_elem.find("hostname")
                if h_elem is not None:
                    hostname = h_elem.get("name")
            
            asset = Asset(
                name=hostname or ip_address,
                ip_address=ip_address,
                tags=["nmap", "discovered"]
            )
            entities.append(asset)

            ports_elem = host.find("ports")
            if ports_elem is not None:
                for port in ports_elem.findall("port"):
                    port_id = int(port.get("portid"))
                    protocol = port.get("protocol")
                    state_elem = port.find("state")
                    state = state_elem.get("state") if state_elem is not None else None
                    service_elem = port.find("service")
                    service_name = service_elem.get("name") if service_elem is not None else None
                    
                    entities.append(Service(
                        asset_id=asset.id,
                        port=port_id,
                        protocol=protocol,
                        name=service_name,
                        state=state
                    ))
        return entities

class NucleiNormalizer(BaseNormalizer):
    """Normalizes Nuclei JSON output into Vulnerability entities."""
    
    def normalize(self, raw_output: str) -> List[SOMBase]:
        vulnerabilities = []
        lines = raw_output.strip().split("\n")
        for line in lines:
            if not line: continue
            try:
                data = json.loads(line)
                info = data.get("info", {})
                vuln = Vulnerability(
                    cve_id=data.get("template-id"),
                    severity=SeverityMapper.normalize(info.get("severity", "unknown")),
                    description=f"{info.get('name', 'Unknown')}: {data.get('matched-at', '')}",
                    asset_id=data.get("ip", "unknown")
                )
                vulnerabilities.append(vuln)
            except json.JSONDecodeError:
                continue
        return vulnerabilities

class NormalizationEngine:
    """Registry and orchestrator for data normalizers."""
    
    _normalizers: Dict[str, BaseNormalizer] = {
        "nmap": NmapNormalizer(),
        "nuclei": NucleiNormalizer()
    }

    @classmethod
    def get_normalizer(cls, tool_name: str) -> Optional[BaseNormalizer]:
        return cls._normalizers.get(tool_name.lower())

    @classmethod
    def normalize_output(cls, tool_name: str, raw_output: str) -> List[SOMBase]:
        normalizer = cls.get_normalizer(tool_name)
        if not normalizer:
            return []
        return normalizer.normalize(raw_output)
