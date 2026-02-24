import json
from typing import Dict, Any, List
from cosf.parser.workflow import WorkflowSchema

class PromptManager:
    """Manages system prompts and context for AI workflow generation."""

    def __init__(self, registered_adapters: Dict[str, Any]):
        self.adapters = registered_adapters

    def get_system_prompt(self) -> str:
        schema = WorkflowSchema.model_json_schema()
        
        adapter_info = []
        for name, adapter in self.adapters.items():
            desc = getattr(adapter, "ADAPTER_DESCRIPTION", "No description available.")
            adapter_info.append(f"- {name}: {desc}")

        adapter_list = "\n".join(adapter_info)

        return f"""You are a Cybersecurity Workflow Architect. 
Your task is to generate a valid YAML workflow for the Cyber Operations Standardization Framework (COSF).

### COSF Workflow Schema (JSON Schema):
{json.dumps(schema, indent=2)}

### Available Adapters:
{adapter_list}

### Instructions:
1. Generate ONLY the YAML content.
2. Ensure the workflow 'name' is descriptive.
3. Tasks should have logical 'id's (e.g., 'scan_local', 'vuln_check').
4. Use 'depends_on' for task ordering.
5. Use variable passing syntax '{{{{ tasks.TASK_ID.outputs.KEY }}}}' when needed.
6. Use 'when' conditions for conditional logic if requested.
7. Be precise with adapter parameters.

Example Output:
name: Network Assessment
tasks:
  - id: discovery
    name: Scan Network
    adapter: nmap
    params: {{target: '192.168.1.0/24'}}
"""

    def get_user_prompt(self, instruction: str) -> str:
        return f"Generate a COSF workflow for the following request: {instruction}"
