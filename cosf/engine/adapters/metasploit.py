from typing import Dict, Any, List
from cosf.engine.adapter import BaseAdapter, TaskResult
from cosf.models.som import AttackStep
try:
    from pymetasploit3.msfrpc import MsfRpcClient
except ImportError:
    MsfRpcClient = None

class MetasploitAdapter(BaseAdapter):
    """Adapter for the Metasploit Framework.
    
    Connects to msfrpcd to execute exploit and auxiliary modules.
    Requires 'host', 'password', 'module_type', 'module_name', and 'options'.
    """
    
    ADAPTER_NAME = "metasploit"
    ADAPTER_DESCRIPTION = "Executes Metasploit modules via MSFRPC."

    async def run(self, params: Dict[str, Any]) -> TaskResult:
        if MsfRpcClient is None:
             raise RuntimeError("pymetasploit3 is not installed. Install it with 'pip install pymetasploit3'")

        host = params.get("host", "127.0.0.1")
        port = params.get("port", 55553)
        user = params.get("user", "msf")
        password = params.get("password")
        ssl = params.get("ssl", True)
        
        module_type = params.get("module_type") # e.g., 'exploit', 'auxiliary'
        module_name = params.get("module_name") # e.g., 'windows/smb/ms17_010_eternalblue'
        options = params.get("options", {})

        if not password:
            raise ValueError("Metasploit adapter requires a 'password' for MSFRPC.")
        if not module_type or not module_name:
            raise ValueError("Metasploit adapter requires 'module_type' and 'module_name'.")

        self.logger.info(f"Connecting to Metasploit RPC at {host}:{port}...")
        
        try:
            client = MsfRpcClient(password, host=host, port=port, username=user, ssl=ssl)
            
            module = client.modules.use(module_type, module_name)
            
            # Set options
            for key, value in options.items():
                module[key] = value

            self.logger.info(f"Executing Metasploit module {module_type}/{module_name}...")
            
            # module.execute returns a dict with 'job_id' and 'uuid'
            execution_res = module.execute()
            job_id = execution_res.get('job_id')
            
            # In a real scenario, we might wait for the job to complete or check sessions
            # For this MVP adapter, we'll record the attempt
            
            attack_step = AttackStep(
                name=f"Metasploit: {module_name}",
                description=f"Executed {module_type} module {module_name} against {options.get('RHOSTS', 'unknown')}",
                status="attempted"
            )

            return TaskResult(
                entities=[attack_step],
                outputs={
                    "job_id": job_id,
                    "uuid": execution_res.get('uuid')
                },
                raw_output=str(execution_res)
            )
        except Exception as e:
            self.logger.error(f"Metasploit execution failed: {e}")
            raise RuntimeError(f"Metasploit error: {e}")
