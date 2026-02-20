import json
from typing import Dict, Any, List
import docker
from cosf.engine.adapter import BaseAdapter
from cosf.models.som import Vulnerability

class NucleiAdapter(BaseAdapter):
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

    async def run(self, params: Dict[str, Any]) -> Dict[str, List[Any]]:
        target = params.get("target")
        if not target:
            raise ValueError("Nuclei adapter requires a 'target' parameter")

        output = await self._run_nuclei(target)
        return self._parse_json(output)

    async def _run_nuclei(self, target: str) -> str:
        if not self.client:
             raise RuntimeError("Docker is not available.")

        container = self.client.containers.run(
            "projectdiscovery/nuclei",
            f"-u {target} -json-export -",
            remove=True
        )
        return container.decode("utf-8")

    def _parse_json(self, output: str) -> Dict[str, List[Any]]:
        vulnerabilities = []
        # Nuclei outputs one JSON object per line or a single line if redirected
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

        return {"vulnerabilities": vulnerabilities}
