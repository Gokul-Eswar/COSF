import re
from typing import Any, Dict

def resolve_variables(context: Dict[str, Any], params: Any) -> Any:
    """Recursively resolves {{ tasks.ID.outputs.KEY }} in params."""
    if isinstance(params, str):
        pattern = r"\{\{\s*tasks\.(\w+)\.outputs\.(\w+)\s*\}\}"
        matches = re.findall(pattern, params)
        for task_id, key in matches:
            val = context.get("tasks", {}).get(task_id, {}).get("outputs", {}).get(key)
            if val is not None:
                params = params.replace(f"{{{{ tasks.{task_id}.outputs.{key} }}}}", str(val))
            else:
                params = params.replace(f"{{{{ tasks.{task_id}.outputs.{key} }}}}", "None")
        return params
    elif isinstance(params, dict):
        return {k: resolve_variables(context, v) for k, v in params.items()}
    elif isinstance(params, list):
        return [resolve_variables(context, i) for i in params]
    return params
