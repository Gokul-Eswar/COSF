import json
from typing import Dict, Any, List, Union
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Vulnerability

class NucleiAdapter(BaseAdapter):
    """Adapter for the Nuclei vulnerability scanner."""
    
    ADAPTER_NAME = "nuclei"

    async def run(self, params: Dict[str, Any]) -> TaskResult:
        target = params.get("target")
        if not target:
            raise ValueError("Nuclei adapter requires a 'target' parameter")

        self.logger.info(f"Running Nuclei scan on target: {target}")
        
        # Use helper from BaseAdapter
        output = self.run_container(
            "projectdiscovery/nuclei",
            f"-u {target} -json-export -"
        )
        
        entities = self._parse_json(output)
        
        return TaskResult(
            entities=entities,
            raw_output=output
        )

    def _parse_json(self, output: str) -> List[Vulnerability]:
        vulnerabilities = []
        # Nuclei outputs one JSON object per line
        lines = output.strip().split("\n")
        for line in lines:
            if not line:
                continue
            try:
                data = json.loads(line)
                info = data.get("info", {})
                vuln = Vulnerability(
                    cve_id=data.get("template-id"),
                    severity=info.get("severity", "unknown"),
                    description=f"{info.get('name', 'Unknown')}: {data.get('matched-at', '')}",
                    asset_id=data.get("ip", "unknown")
                )
                vulnerabilities.append(vuln)
            except json.JSONDecodeError:
                continue

        return vulnerabilities
