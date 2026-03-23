import ipaddress
import datetime
from typing import List, Any, Dict, Set, Optional, Tuple
from abc import ABC, abstractmethod
from cosf.models.som import Relationship, Asset, Service, Credential, Vulnerability
from cosf.parser.workflow import WorkflowSchema, WorkflowTask

class InferenceRule(ABC):
    """Base class for security inference rules."""
    @abstractmethod
    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        pass

class NetworkProximityRule(InferenceRule):
    """Infers relationships between assets in the same network subnet."""
    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        relationships = []
        assets = entities.get("assets", [])
        
        # Group assets by /24 subnet (standard CIDR for proximity inference)
        subnet_map: Dict[str, Set[str]] = {}
        for a in assets:
            if not a.ip_address: continue
            try:
                ip = ipaddress.ip_address(str(a.ip_address))
                # Create a /24 subnet key
                if isinstance(ip, ipaddress.IPv4Address):
                    network = ipaddress.IPv4Network(f"{str(ip)}/24", strict=False)
                    key = str(network)
                    if key not in subnet_map:
                        subnet_map[key] = set()
                    subnet_map[key].add(a.id)
            except ValueError:
                continue

        for key, asset_ids in subnet_map.items():
            if len(asset_ids) > 1:
                asset_list = list(asset_ids)
                for i in range(len(asset_list)):
                    for j in range(i + 1, len(asset_list)):
                        relationships.append(Relationship(
                            source_id=asset_list[i],
                            target_id=asset_list[j],
                            type="NETWORK_PROXIMITY",
                            metadata={"subnet": key, "source": "inference"}
                        ))
        return relationships

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

class CrossToolCorrelationRule(InferenceRule):
    """Correlates data from different tools (e.g., Nmap, Nuclei, Shodan)."""
    
    def apply(self, entities: Dict[str, List[Any]]) -> List[Relationship]:
        relationships = []
        assets = entities.get("assets", [])
        services = entities.get("services", [])
        vulns = entities.get("vulnerabilities", [])
        
        # Link Shodan external findings to internal assets
        for asset in assets:
            if asset.tags and "shodan" in asset.tags:
                relationships.append(Relationship(
                    source_id="shodan_external",
                    target_id=asset.id,
                    type="EXTERNAL_VISIBILITY",
                    metadata={"source": "shodan_correlation"}
                ))

        # Correlate specific services (Nmap) with vulnerabilities (Nuclei)
        # Often Nuclei finds a vuln but doesn't explicitly link it to a service entity
        for v in vulns:
            for s in services:
                if v.asset_id == s.asset_id and s.port in (v.description or ""):
                    relationships.append(Relationship(
                        source_id=s.id,
                        target_id=v.id,
                        type="SERVICE_VULNERABILITY",
                        metadata={"source": "cross_tool_correlation"}
                    ))
        
        return relationships

class InferenceEngine:
    """Orchestrates security inference rules to discover hidden relationships."""
    
    def __init__(self):
        self.rules: List[InferenceRule] = [
            NetworkProximityRule(),
            CredentialReuseRule(),
            ServiceMatchingRule(),
            ExploitMappingRule(),
            CrossToolCorrelationRule()
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

    def suggest_remediations(self, entities: Dict[str, List[Any]]) -> List[WorkflowTask]:
        """Suggests remediation tasks based on discovered vulnerabilities."""
        suggestions = []
        vulns = entities.get("vulnerabilities", [])
        assets = {a.id: a for a in entities.get("assets", [])}
        
        for v in vulns:
            asset = assets.get(v.asset_id)
            if not asset: continue
            
            # Simple mapping: Critical/High vulns suggest patching
            if v.severity.lower() in ("critical", "high"):
                suggestions.append(WorkflowTask(
                    id=f"remediate_{v.id}",
                    name=f"Auto-Remediate: {v.cve_id or v.description[:20]}",
                    adapter="remediation",
                    params={
                        "action": "patch_vulnerability",
                        "target": str(asset.ip_address),
                        "cve_id": v.cve_id
                    }
                ))
        
        return suggestions

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

    def calculate(self, entities: Dict[str, List[Any]], graph: Optional[Any] = None) -> Dict[str, float]:
        """Calculates risk scores for all assets, optionally using graph centrality for blast radius."""
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

            # 3. Blast Radius calculation (Centrality-based impact)
            if graph and asset.id in graph:
                # Degree centrality (number of connections) as impact proxy
                # Out-degree is particularly relevant: what can this asset reach?
                out_degree = graph.out_degree(asset.id)
                score += min(out_degree * 0.2, 2.0) # Cap at +2.0

            # Cap the final score at 10.0
            scores[asset.id] = min(score, 10.0)
            
        return scores

class TemporalAnalysisEngine:
    """Analyzes security posture changes over time."""
    
    def analyze_posture_drift(self, snapshots: List[Tuple[datetime.datetime, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Identifies significant changes between execution snapshots."""
        drifts = []
        if len(snapshots) < 2:
            return drifts
            
        # Sort by timestamp
        snapshots.sort(key=lambda x: x[0])
        
        for i in range(1, len(snapshots)):
            prev_time, prev_data = snapshots[i-1]
            curr_time, curr_data = snapshots[i]
            
            # Simple drift detection on risk scores
            prev_scores = prev_data.get("risk_scores", {})
            curr_scores = curr_data.get("risk_scores", {})
            
            for asset_id, curr_score in curr_scores.items():
                prev_score = prev_scores.get(asset_id)
                if prev_score is not None and abs(curr_score - prev_score) > 1.0:
                    drifts.append({
                        "asset_id": asset_id,
                        "previous_score": prev_score,
                        "current_score": curr_score,
                        "timestamp": curr_time.isoformat(),
                        "drift_type": "RISK_SCORE_CHANGE"
                    })
        return drifts
