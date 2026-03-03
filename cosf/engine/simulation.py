import random
import uuid
from typing import List, Dict, Any, Union
from cosf.models.som import Asset, Service, Vulnerability, SOMBase
from cosf.engine.adapter import TaskResult

class MockResponseGenerator:
    """Generates realistic SOM entities for simulation mode."""

    @staticmethod
    def generate(adapter_name: str, params: Dict[str, Any]) -> TaskResult:
        """Generates a TaskResult with mock entities based on the adapter."""
        target = params.get("target", "127.0.0.1")
        
        # Ensure we have a valid mock IP for SOM Asset requirements
        mock_ip = target
        is_valid_ip = all(c in "0123456789.:abcdef" for c in target.lower()) and (target.count(".") == 3 or ":" in target)
        if not is_valid_ip:
            mock_ip = f"192.168.1.{random.randint(2, 254)}"

        entities: List[SOMBase] = []
        outputs: Dict[str, Any] = {"status": "simulated"}

        if adapter_name == "nmap":
            # Generate a mock Asset
            asset = Asset(
                name=f"mock-host-{target.replace('.', '-').replace(':', '-')}",
                ip_address=mock_ip,
                os=random.choice(["Linux 5.x", "Windows 10", "Ubuntu 22.04"]),
                tags=["simulated", "nmap"]
            )
            entities.append(asset)
            outputs["target_ip"] = str(asset.ip_address)

            # Generate some mock Services
            common_ports = [(22, "ssh"), (80, "http"), (443, "https"), (3306, "mysql"), (5432, "postgresql")]
            for port, name in random.sample(common_ports, k=random.randint(1, 3)):
                entities.append(Service(
                    asset_id=asset.id,
                    port=port,
                    protocol="tcp",
                    name=name,
                    state="open"
                ))

        elif adapter_name == "nuclei":
            # Generate mock Vulnerabilities
            vuln_types = [
                ("cve-2021-44228", "Log4j Remote Code Execution", "Critical"),
                ("cve-2023-1234", "Reflected Cross-Site Scripting", "Medium"),
                ("http-missing-security-headers", "Missing Security Headers", "Low"),
                ("exposed-git-directory", "Exposed .git Directory", "High")
            ]
            
            for cve, desc, severity in random.sample(vuln_types, k=random.randint(1, 2)):
                entities.append(Vulnerability(
                    cve_id=cve,
                    severity=severity,
                    description=f"[SIMULATED] {desc} on {target}",
                    asset_id=mock_ip # Use mock_ip instead of raw target
                ))

        elif adapter_name == "mock":
            # Generate generic mock entities
            asset = Asset(
                name=f"mock-host-{target}",
                ip_address=mock_ip,
                tags=["simulated", "mock"]
            )
            entities.append(asset)
            outputs["target_ip"] = str(asset.ip_address)
            outputs["ip"] = str(asset.ip_address) # Alias for common usage

            entities.append(Service(
                asset_id=asset.id,
                port=80,
                protocol="tcp",
                name="http",
                state="open"
            ))

        elif adapter_name == "aws":
            # Generate mock AWS Assets
            for i in range(random.randint(1, 3)):
                entities.append(Asset(
                    name=f"i-0abcdef123456789{i}",
                    ip_address=f"10.0.0.{10+i}",
                    os="Amazon Linux 2",
                    tags=["simulated", "aws", "ec2"]
                ))

        else:
            # Default fallback for unknown adapters
            outputs["message"] = f"No specific mock generator for adapter '{adapter_name}'"

        return TaskResult(
            entities=entities,
            outputs=outputs,
            raw_output=f"""--- SIMULATED OUTPUT FOR {adapter_name.upper()} ---
Target: {target}
Status: Success"""
        )
