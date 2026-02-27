import json
from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Vulnerability

class ZapAdapter(BaseAdapter):
    """Adapter for the OWASP ZAP web vulnerability scanner."""
    
    ADAPTER_NAME = "zap"
    ADAPTER_DESCRIPTION = "Performs dynamic application security testing (DAST) using OWASP ZAP. Requires 'target' URL."

    async def run(self, params: Dict[str, Any], dry_run: bool = False) -> TaskResult:
        target = params.get("target")
        if not target:
            raise ValueError("Zap adapter requires a 'target' parameter (URL)")

        self.logger.info(f"Running ZAP baseline scan on target: {target}")
        
        # We use zap-baseline.py for a quick scan and export to JSON
        # Note: -J specifies the json report file inside the container
        # Since we need the output, we'll try to get it from stdout or a shared volume.
        # For simplicity in this adapter, we'll use zap-cli if possible or parse the json output.
        
        # Command to run baseline scan and output json to stdout
        command = f"zap-baseline.py -t {target} -J report.json && cat /zap/wrk/report.json"
        
        try:
            # Note: zap-baseline.py usually returns non-zero if it finds anything.
            # We might need to handle that or use a more robust way to get the report.
            raw_output = self.run_container(
                "owasp/zap2docker-stable",
                command,
                user="root" # Ensure we can write the report
            )
            
            entities = self._parse_zap_json(raw_output)
            
            return TaskResult(
                entities=entities,
                raw_output=raw_output
            )
        except Exception as e:
            self.logger.error(f"ZAP execution failed: {e}")
            raise

    def _parse_zap_json(self, json_content: str) -> List[Vulnerability]:
        vulnerabilities = []
        try:
            # Extract only the JSON part if there's surrounding text
            start = json_content.find('{')
            end = json_content.rfind('}') + 1
            if start == -1 or end == 0:
                return []
            
            data = json.loads(json_content[start:end])
            site_data = data.get("site", [])
            if isinstance(site_data, dict): site_data = [site_data]

            for site in site_data:
                alerts = site.get("alerts", [])
                for alert in alerts:
                    vuln = Vulnerability(
                        cve_id=alert.get("pluginid"),
                        severity=alert.get("riskdesc", "unknown").split(" ")[0].lower(),
                        description=f"{alert.get('name')}: {alert.get('desc')}",
                        asset_id=site.get("@host")
                    )
                    vulnerabilities.append(vuln)
        except Exception as e:
            self.logger.error(f"Failed to parse ZAP JSON: {e}")
            
        return vulnerabilities
