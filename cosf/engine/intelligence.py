from typing import List, Any, Dict, Set, Optional
from abc import ABC, abstractmethod
from cosf.models.som import Relationship, Asset, Service, Credential, Vulnerability
from cosf.parser.workflow import WorkflowSchema, WorkflowTask

class InferenceRule(ABC):
    """Base class for security inference rules."""
    @abstractmethod
    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        pass

class CredentialReuseRule(InferenceRule):
    """Infers relationships between assets that share the same credentials."""
    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        relationships = []
        creds = entities.get("credentials", [])
        
        # Group assets by username/password hash or password
        cred_map: Dict[str, Set[str]] = {}
        for c in creds:
            if not c.asset_id: continue
            
            # Use username + (password or hash) as a unique credential key
            key = f"{c.username}:{c.password or c.password_hash}"
            if key not in cred_map:
                cred_map[key] = set()
            cred_map[key].add(c.asset_id)

        for key, asset_ids in cred_map.items():
            if len(asset_ids) > 1:
                asset_list = list(asset_ids)
                for i in range(len(asset_list)):
                    for j in range(i + 1, len(asset_list)):
                        relationships.append(Relationship(
                            source_id=asset_list[i],
                            target_id=asset_list[j],
                            type="CREDENTIAL_REUSE",
                            metadata={"credential_key": key, "source": "inference"}
                        ))
        return relationships

class ServiceMatchingRule(InferenceRule):
    """Infers relationships between assets running the same services."""
    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        relationships = []
        services = entities.get("services", [])
        
        # Group assets by service name and port
        service_map: Dict[str, Set[str]] = {}
        for s in services:
            key = f"{s.name}:{s.port}:{s.protocol}"
            if key not in service_map:
                service_map[key] = set()
            service_map[key].add(s.asset_id)

        for key, asset_ids in service_map.items():
            if len(asset_ids) > 1:
                asset_list = list(asset_ids)
                for i in range(len(asset_list)):
                    for j in range(i + 1, len(asset_list)):
                        relationships.append(Relationship(
                            source_id=asset_list[i],
                            target_id=asset_list[j],
                            type="SAME_SERVICE",
                            metadata={"service_key": key, "source": "inference"}
                        ))
        return relationships

class ExploitMappingRule(InferenceRule):
    """Infers relationships between vulnerabilities and Metasploit modules."""
    
    # Mapping of Nuclei template IDs (or CVEs) to Metasploit modules
    VULN_TO_MSF = {
        "cve-2021-44228": "exploit/multi/http/log4shell_header_injection",
        "cve-2017-0144": "exploit/windows/smb/ms17_010_eternalblue",
        "cve-2019-0708": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
        "cve-2020-0796": "exploit/windows/smb/ms20_0796_smbv3_compression",
        "cve-2014-0160": "auxiliary/scanner/ssl/ssl_heartbleed"
    }

    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        relationships = []
        vulns = entities.get("vulnerabilities", [])
        
        for v in vulns:
            if not v.cve_id: continue
            
            cve_id = v.cve_id.lower()
            if cve_id in self.VULN_TO_MSF:
                msf_module = self.VULN_TO_MSF[cve_id]
                relationships.append(Relationship(
                    source_id=v.id,
                    target_id=msf_module, # Note: This target might be a virtual node or a module ID
                    type="EXPLOITABLE_VIA",
                    metadata={"msf_module": msf_module, "source": "inference"}
                ))
        return relationships

class InferenceEngine:
    """Orchestrates security inference rules to discover hidden relationships."""
    
    def __init__(self):
        self.rules: List[InferenceRule] = [
            CredentialReuseRule(),
            ServiceMatchingRule(),
            ExploitMappingRule()
        ]
        self.scorer = RiskScorer()

    def infer_relationships(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        """Applies all rules to the provided entities and returns inferred relationships."""
        all_inferred = []
        for rule in self.rules:
            all_inferred.extend(rule.apply(entities))
        return all_inferred

    def calculate_risk_scores(self, entities: Dict[str, List[Any]]) -> Dict[str, float]:
        """Calculates risk scores for all assets."""
        return self.scorer.calculate(entities)

    def validate_attack_path(self, path: List[str], entities: Dict[str, List[Any]]) -> Optional[WorkflowSchema]:
        """Generates a COSF workflow to validate a discovered attack path."""
        if not path: return None
        
        tasks = []
        vulns = {v.id: v for v in entities.get("vulnerabilities", [])}
        assets = {a.id: a for a in entities.get("assets", [])}
        
        exploit_rule = ExploitMappingRule()
        
        for i, node_id in enumerate(path):
            if node_id in vulns:
                v = vulns[node_id]
                cve_id = v.cve_id.lower() if v.cve_id else None
                if cve_id in exploit_rule.VULN_TO_MSF:
                    msf_module = exploit_rule.VULN_TO_MSF[cve_id]
                    asset = assets.get(v.asset_id)
                    if asset:
                        tasks.append(WorkflowTask(
                            id=f"validate_{v.id}",
                            name=f"Validate Exploit: {v.cve_id}",
                            adapter="metasploit",
                            params={
                                "module_type": msf_module.split("/")[0],
                                "module_name": "/".join(msf_module.split("/")[1:]),
                                "options": {"RHOSTS": str(asset.ip_address)}
                            }
                        ))
        
        if not tasks: return None
        
        return WorkflowSchema(
            name=f"Attack Path Validation: {' -> '.join(path[:3])}...",
            tasks=tasks
        )

class RiskScorer:
    """Calculates security risk scores for assets based on their characteristics and findings."""

    def calculate(self, entities: Dict[str, List[Any]]) -> Dict[str, float]:
        scores = {}
        assets = entities.get("assets", [])
        services = entities.get("services", [])
        vulns = entities.get("vulnerabilities", [])
        
        # Group data by asset_id for efficient lookup
        asset_services: Dict[str, List[Service]] = {}
        for s in services:
            if s.asset_id not in asset_services: asset_services[s.asset_id] = []
            asset_services[s.asset_id].append(s)

        asset_vulns: Dict[str, List[Vulnerability]] = {}
        for v in vulns:
            if v.asset_id not in asset_vulns: asset_vulns[v.asset_id] = []
            asset_vulns[v.asset_id].append(v)

        # Pre-check for exploitable vulns
        exploit_rule = ExploitMappingRule()
        inferred_rels = exploit_rule.apply(entities)
        exploitable_vuln_ids = {r.source_id for r in inferred_rels}

        for asset in assets:
            score = 1.0 # Base score
            
            # 1. Service Factor (more exposure = higher risk)
            s_count = len(asset_services.get(asset.id, []))
            score += min(s_count * 0.5, 3.0) # Cap at +3.0

            # 2. Vulnerability Factor (severity based)
            a_vulns = asset_vulns.get(asset.id, [])
            for v in a_vulns:
                v_weight = 0.0
                if v.severity.lower() == "critical": v_weight = 4.0
                elif v.severity.lower() == "high": v_weight = 2.5
                elif v.severity.lower() == "medium": v_weight = 1.0
                elif v.severity.lower() == "low": v_weight = 0.2
                
                # Bonus weight for exploitable vulnerabilities
                if v.id in exploitable_vuln_ids:
                    v_weight *= 1.5
                
                score += v_weight

            # 3. Credential reuse factor (if we had inferred relationships available here)
            # This would require more complex cross-entity logic

            # Cap the final score at 10.0
            scores[asset.id] = min(score, 10.0)
            
        return scores
