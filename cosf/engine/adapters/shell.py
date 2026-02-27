import asyncio
import subprocess
from typing import Dict, Any, List, Union
from cosf.engine.adapter import BaseAdapter, TaskResult

class ShellAdapter(BaseAdapter):
    """A generic adapter for running local shell commands.
    
    WARNING: This adapter allows execution of arbitrary commands. 
    Use with caution and ensure input is validated or comes from a trusted source.
    """
    
    ADAPTER_NAME = "shell"
    ADAPTER_DESCRIPTION = "Executes arbitrary shell commands on the host system."

    async def run(self, params: Dict[str, Any], dry_run: bool = False) -> TaskResult:
        command = params.get("command")
        if not command:
            raise ValueError("Shell adapter requires a 'command' parameter.")

        self.logger.info(f"Executing shell command: {command}")
        
        try:
            # Run the command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            stdout_str = stdout.decode("utf-8").strip()
            stderr_str = stderr.decode("utf-8").strip()
            
            if process.returncode != 0:
                self.logger.warning(f"Command failed with exit code {process.returncode}")
                # We still return the output as it might contain useful info
            
            return TaskResult(
                entities=[], # Shell adapter doesn't automatically parse entities yet
                outputs={
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "exit_code": process.returncode
                },
                raw_output=stdout_str if stdout_str else stderr_str
            )
        except Exception as e:
            self.logger.error(f"Failed to execute shell command: {e}")
            raise RuntimeError(f"Shell execution failed: {e}")
