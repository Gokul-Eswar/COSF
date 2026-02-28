import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime
import ipaddress

class PolicyEngine:
    """Enforces safety constraints and policies on workflow execution."""

    def __init__(self, config_path: str = "safety_config.yaml"):
        self.config_path = config_path
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {
                "restricted_ips": [],
                "allowed_times": {"start": "00:00", "end": "23:59"},
                "restricted_adapters": []
            }

    def check_task(self, adapter: str, params: Dict[str, Any]) -> List[str]:
        """Checks a task against the policy and returns a list of violations."""
        violations = []
        
        # 1. Check restricted adapters
        if adapter in self.policy.get("restricted_adapters", []):
            violations.append(f"Adapter '{adapter}' is restricted by policy.")

        # 2. Check restricted IPs
        target = params.get("target") or params.get("ip_address")
        if target:
            restricted_ips = self.policy.get("restricted_ips", [])
            try:
                target_ip = ipaddress.ip_address(target)
                for restricted in restricted_ips:
                    if target_ip in ipaddress.ip_network(restricted):
                        violations.append(f"Target IP '{target}' is restricted by policy ('{restricted}').")
            except ValueError:
                # Target might be a hostname, skip IP check for now or resolve it
                pass

        # 3. Check allowed times
        allowed_times = self.policy.get("allowed_times", {})
        if allowed_times:
            now = datetime.now().time()
            start_time = datetime.strptime(allowed_times.get("start", "00:00"), "%H:%M").time()
            end_time = datetime.strptime(allowed_times.get("end", "23:59"), "%H:%M").time()
            
            if not (start_time <= now <= end_time):
                violations.append(f"Execution outside of allowed time window ({allowed_times['start']} - {allowed_times['end']}).")

        return violations

    def check_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Checks an entire plan and returns a mapping of task IDs to violations."""
        results = {}
        for task in plan:
            violations = self.check_task(task["adapter"], task.get("params", {}))
            if violations:
                results[task["id"]] = violations
        return results
