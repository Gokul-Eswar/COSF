# COSF Adapter Ecosystem

This directory contains the pluggable adapters that allow the COSF engine to communicate with various security tools.

## Supported Adapters

### Discovery & Scanning
- **nmap**: Network discovery and service mapping.
    - `target`: (Required) IP address or hostname.
- **nuclei**: Template-based vulnerability scanner.
    - `target`: (Required) URL, IP, or hostname.
- **aws**: Infrastructure reconnaissance and security posture checks.
    - `operation`: (Required) The operation to perform (e.g., `s3_list_buckets`).
    - `region`: (Optional) AWS region (Default: `us-east-1`).
    - `aws_access_key_id`: (Optional) Can also be set via environment.
    - `aws_secret_access_key`: (Optional) Can also be set via environment.

### Web Application Security
- **zap**: Dynamic Application Security Testing (DAST) using OWASP ZAP.
    - `target`: (Required) URL of the application.
- **burp**: Integration with Burp Suite REST API.
    - `target`: (Required) URL to scan.
    - `api_url`: (Optional) Base URL for Burp REST API (Default: `http://127.0.0.1:1337`).
    - `api_key`: (Optional) API key for authentication.

### Offensive & Exploitation
- **metasploit**: Execution of modules via MSFRPC.
    - `module_type`: (Required) 'exploit', 'auxiliary', 'post', etc.
    - `module_name`: (Required) Full path of the module.
    - `password`: (Required) MSFRPC password.
    - `options`: (Required) Dictionary of module options (e.g., `RHOSTS`, `LHOST`).
    - `host`: (Optional) MSFRPC host (Default: `127.0.0.1`).

### Utilities & Custom Logic
- **python**: Run custom Python scripts within the engine context.
    - `script`: (Required) The Python code to execute.
- **shell**: Execute arbitrary shell commands on the host.
    - `command`: (Required) The shell command string.
- **mock**: Returns simulated data for testing and demonstration.

## Creating New Adapters

To create a new adapter:
1. Create a new `.py` file in this directory.
2. Inherit from `cosf.engine.adapter.BaseAdapter`.
3. Set `ADAPTER_NAME` and `ADAPTER_DESCRIPTION`.
4. Implement the `async def run(self, params: Dict[str, Any]) -> TaskResult` method.
5. (Optional) Implement a private method to parse tool output into **Security Object Model (SOM)** entities.
