from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
import xml.etree.ElementTree as ET
import json
import re
from cosf.models.som import Asset, Service, Vulnerability, SOMBase, Evidence

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
        "note": "Low",
        # ZAP specific
        "informational": "Info"
    }

    @classmethod
    def normalize(cls, severity: str) -> str:
        if not severity: return "Unknown"
        # Handle formats like "3 (High)" or "High (3)" from ZAP
        clean_severity = severity.lower()
        
        # Check for direct keywords first
        for key in cls.MAPPING.keys():
            if key in clean_severity:
                return cls.MAPPING[key]
        
        if "(" in clean_severity:
            match = re.search(r"\((.*?)\)", clean_severity)
            if match:
                clean_severity = match.group(1).strip()
                if clean_severity in cls.MAPPING:
                    return cls.MAPPING[clean_severity]
        
        return cls.MAPPING.get(clean_severity, "Unknown")

class FingerprintRule:
    """Standardizes OS and service version strings."""
    
    @classmethod
    def normalize_os(cls, raw_os: Optional[str]) -> Optional[str]:
        if not raw_os: return None
        # Example: "Linux 3.10 - 4.11" -> "Linux"
        # Example: "Microsoft Windows 10 1709 - 1903" -> "Windows 10"
        low_os = raw_os.lower()
        if "windows" in low_os:
            if "11" in low_os: return "Windows 11"
            if "10" in low_os: return "Windows 10"
            if "2019" in low_os: return "Windows Server 2019"
            if "2016" in low_os: return "Windows Server 2016"
            return "Windows"
        if "linux" in low_os:
            if "amazon" in low_os or "amzn" in low_os: return "Amazon Linux"
            if "ubuntu" in low_os: return "Ubuntu Linux"
            if "debian" in low_os: return "Debian Linux"
            if "centos" in low_os: return "CentOS Linux"
            return "Linux"
        if "macos" in low_os or "darwin" in low_os:
            return "macOS"
        return raw_os

    @classmethod
    def normalize_version(cls, version: Optional[str]) -> Optional[str]:
        if not version: return None
        # Clean up common noise in version strings
        return version.split(" (")[0].strip()

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
            
            # Extract OS information
            os_name = None
            os_elem = host.find("os")
            if os_elem is not None:
                os_match = os_elem.find("osmatch")
                if os_match is not None:
                    os_name = os_match.get("name")
            
            asset = Asset(
                name=hostname or ip_address,
                ip_address=ip_address,
                os=FingerprintRule.normalize_os(os_name),
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
                    service_name = None
                    product = None
                    version = None
                    
                    if service_elem is not None:
                        service_name = service_elem.get("name")
                        product = service_elem.get("product")
                        version = FingerprintRule.normalize_version(service_elem.get("version"))
                    
                    entities.append(Service(
                        asset_id=asset.id,
                        port=port_id,
                        protocol=protocol,
                        name=service_name,
                        product=product,
                        version=version,
                        state=state
                    ))
        return entities

class NucleiNormalizer(BaseNormalizer):
    """Normalizes Nuclei JSON output into Vulnerability entities with Evidence mapping."""
    
    def normalize(self, raw_output: str) -> List[SOMBase]:
        entities = []
        lines = raw_output.strip().split("\n")
        import hashlib
        for line in lines:
            if not line: continue
            try:
                data = json.loads(line)
                info = data.get("info", {})
                
                # Create Evidence for this finding
                evidence = Evidence(
                    name=f"Nuclei finding: {data.get('template-id')}",
                    type="log",
                    file_path="", # In-memory evidence from raw tool log line
                    hash_sha256=hashlib.sha256(line.encode()).hexdigest(),
                    metadata={"raw_line": data}
                )
                entities.append(evidence)

                vuln = Vulnerability(
                    cve_id=data.get("template-id"),
                    severity=SeverityMapper.normalize(info.get("severity", "unknown")),
                    description=f"{info.get('name', 'Unknown')}: {data.get('matched-at', '')}",
                    asset_id=data.get("ip", "unknown")
                )
                # Link Evidence to Vulnerability SOM is missing evidence_ids but database model has it.
                # Actually, SOM AttackStep has evidence_ids. We'll use metadata for now or update SOM.
                # For this track, we'll store it as a related entity.
                entities.append(vuln)
            except json.JSONDecodeError:
                continue
        return entities

class ZapNormalizer(BaseNormalizer):
    """Normalizes OWASP ZAP JSON output into Vulnerability entities with Evidence mapping."""
    
    def normalize(self, raw_output: str) -> List[SOMBase]:
        entities = []
        import hashlib
        try:
            start = raw_output.find('{')
            end = raw_output.rfind('}') + 1
            if start == -1 or end == 0: return []
            
            data = json.loads(raw_output[start:end])
            site_data = data.get("site", [])
            if isinstance(site_data, dict): site_data = [site_data]

            for site in site_data:
                host = site.get("@host")
                alerts = site.get("alerts", [])
                for alert in alerts:
                    # Create Evidence for each alert
                    evidence = Evidence(
                        name=f"ZAP Alert: {alert.get('name')}",
                        type="log",
                        file_path="",
                        hash_sha256=hashlib.sha256(json.dumps(alert).encode()).hexdigest(),
                        metadata={"alert_data": alert}
                    )
                    entities.append(evidence)

                    vuln = Vulnerability(
                        cve_id=alert.get("pluginid"),
                        severity=SeverityMapper.normalize(alert.get("riskdesc", "unknown")),
                        description=f"{alert.get('name')}: {alert.get('desc')}",
                        asset_id=host or "unknown"
                    )
                    entities.append(vuln)
        except Exception:
            pass
        return entities

class BurpNormalizer(BaseNormalizer):
    """Normalizes Burp Suite REST API findings."""
    
    def normalize(self, raw_output: str) -> List[SOMBase]:
        vulnerabilities = []
        try:
            data = json.loads(raw_output)
            issues = []
            if isinstance(data, list):
                issues = data
            elif isinstance(data, dict):
                issues = data.get("issue_events", []) or data.get("issues", [])
                if not issues and "severity" in data:
                    issues = [data]

            for issue in issues:
                severity = issue.get("severity") or issue.get("risk")
                vuln = Vulnerability(
                    cve_id=str(issue.get("issue_type_id", "")),
                    severity=SeverityMapper.normalize(severity),
                    description=f"{issue.get('name', 'Unknown')}: {issue.get('description', 'No description')}",
                    asset_id=issue.get("host") or "unknown"
                )
                vulnerabilities.append(vuln)
        except Exception:
            pass
        return vulnerabilities

class MetasploitNormalizer(BaseNormalizer):
    """Normalizes Metasploit execution results into AttackStep entities."""
    
    def normalize(self, raw_output: str) -> List[SOMBase]:
        from cosf.models.som import AttackStep
        entities = []
        try:
            if raw_output.startswith("{"):
                data = json.loads(raw_output.replace("'", "\""))
                if "job_id" in data or "uuid" in data:
                    entities.append(AttackStep(
                        name="Metasploit Execution",
                        description=f"Job {data.get('job_id')} (UUID: {data.get('uuid')}) initiated.",
                        status="attempted"
                    ))
        except Exception:
            pass
        return entities

class NormalizationEngine:
    """Registry and orchestrator for data normalizers."""
    
    _normalizers: Dict[str, BaseNormalizer] = {
        "nmap": NmapNormalizer(),
        "nuclei": NucleiNormalizer(),
        "zap": ZapNormalizer(),
        "burp": BurpNormalizer(),
        "metasploit": MetasploitNormalizer()
    }

    @classmethod
    def register_normalizer(cls, tool_name: str, normalizer: BaseNormalizer):
        """Registers a new normalizer dynamically."""
        cls._normalizers[tool_name.lower()] = normalizer

    @classmethod
    def get_normalizer(cls, tool_name: str) -> Optional[BaseNormalizer]:
        return cls._normalizers.get(tool_name.lower())

    @classmethod
    def normalize_output(cls, tool_name: str, raw_output: str) -> List[SOMBase]:
        normalizer = cls.get_normalizer(tool_name)
        if not normalizer:
            return []
        return normalizer.normalize(raw_output)


