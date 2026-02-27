import json
from typing import Dict, Any, List, Union
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import Vulnerability
from cosf.engine.normalization import NormalizationEngine

class NucleiAdapter(BaseAdapter):
    """Adapter for the Nuclei vulnerability scanner."""
    
    ADAPTER_NAME = "nuclei"
    ADAPTER_DESCRIPTION = "Template-based vulnerability scanner. Requires 'target' parameter (URL or IP)."

    async def run(self, params: Dict[str, Any], dry_run: bool = False) -> TaskResult:
        target = params.get("target")
        if not target:
            raise ValueError("Nuclei adapter requires a 'target' parameter")

        self.logger.info(f"Running Nuclei scan on target: {target}")
        
        # Use helper from BaseAdapter
        output = self.run_container(
            "projectdiscovery/nuclei",
            f"-u {target} -json-export -"
        )
        
        entities = NormalizationEngine.normalize_output("nuclei", output)
        
        return TaskResult(
            entities=entities,
            raw_output=output
        )
