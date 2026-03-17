import json
import base64
from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult

class PythonAdapter(BaseAdapter):
    """Adapter for running custom Python scripts."""
    
    ADAPTER_NAME = "python"
    ADAPTER_DESCRIPTION = "Runs a custom Python script. Requires 'script' (base64 encoded or raw string) and returns TaskResult compatible JSON."

    async def _run(self, params: Dict[str, Any]) -> TaskResult:
        script_content = params.get("script")
        if not script_content:
            raise ValueError("Python adapter requires a 'script' parameter")

        # Handle base64 encoded scripts for easier YAML embedding
        try:
            if params.get("base64", False):
                script_content = base64.b64decode(script_content).decode("utf-8")
        except Exception:
            pass

        self.logger.info("Executing custom Python script")
        
        # We run the script in a python container.
        # We'll pass the script as a command or via a temporary file.
        # For simplicity here, we'll pass it via stdin to python -c
        
        # Ensure the script prints a JSON object at the end
        command = f'python3 -c "{script_content}"'
        
        try:
            raw_output = self.run_container(
                "python:3.12-slim",
                ["python3", "-c", script_content]
            )
            
            # The script MUST output a JSON object representing TaskResult
            try:
                data = json.loads(raw_output)
                return TaskResult(**data)
            except json.JSONDecodeError:
                return TaskResult(
                    entities=self.normalize(raw_output),
                    raw_output=raw_output, 
                    outputs={"info": "Script executed. Data parsed via fallback normalizer."}
                )
                
        except Exception as e:
            self.logger.error(f"Python script execution failed: {e}")
            raise
