from typing import List, Any, Dict, Set
from abc import ABC, abstractmethod
from cosf.models.som import Relationship, Asset, Service, Credential, Vulnerability

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

class InferenceEngine:
    """Orchestrates security inference rules to discover hidden relationships."""
    
    def __init__(self):
        self.rules: List[InferenceRule] = [
            CredentialReuseRule(),
            ServiceMatchingRule()
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

        for asset in assets:
            score = 1.0 # Base score
            
            # 1. Service Factor (more exposure = higher risk)
            s_count = len(asset_services.get(asset.id, []))
            score += min(s_count * 0.5, 3.0) # Cap at +3.0

            # 2. Vulnerability Factor (severity based)
            a_vulns = asset_vulns.get(asset.id, [])
            for v in a_vulns:
                if v.severity.lower() == "critical": score += 4.0
                elif v.severity.lower() == "high": score += 2.5
                elif v.severity.lower() == "medium": score += 1.0
                elif v.severity.lower() == "low": score += 0.2

            # Cap the final score at 10.0
            scores[asset.id] = min(score, 10.0)
            
        return scores
