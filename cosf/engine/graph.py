import networkx as nx
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from cosf.models.database import DBAsset, DBService, DBVulnerability, DBCredential, DBRelationship
from cosf.models.db_session import AsyncSessionLocal
from cosf.engine.intelligence import InferenceEngine, ExploitMappingRule
from cosf.models.som import Asset, Service, Vulnerability, Credential, Relationship

class GraphEngine:
    """Engine for building and analyzing security relationship graphs."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.intelligence = InferenceEngine()

    async def build_from_db(self, infer: bool = False):
        """Builds the graph by fetching all relevant entities and relationships from the DB."""
        self.graph.clear()
        
        # Add a virtual "Internet" node as a potential attack source
        self.graph.add_node("internet", type="source", label="Internet", category="external")

        async with AsyncSessionLocal() as session:
            # 1. Load Nodes
            entities_for_inference = {
                "assets": [],
                "services": [],
                "vulnerabilities": [],
                "credentials": []
            }

            assets = await session.execute(select(DBAsset))
            for a in assets.scalars():
                self.graph.add_node(a.id, type="asset", label=a.name, ip=a.ip_address, os=a.os, risk_score=a.risk_score)
                entities_for_inference["assets"].append(Asset(id=a.id, name=a.name, ip_address=a.ip_address, os=a.os))

            services = await session.execute(select(DBService))
            for s in services.scalars():
                self.graph.add_node(s.id, type="service", label=f"{s.protocol}/{s.port}", name=s.name)
                # Implicit relationship: Asset HAS Service
                self.graph.add_edge(s.asset_id, s.id, type="HAS_SERVICE")
                
                # If service is common web or external, link from Internet (heuristic)
                if s.port in [80, 443, 8080, 22]:
                    self.graph.add_edge("internet", s.id, type="ACCESSIBLE_FROM", weight=0.5)
                
                entities_for_inference["services"].append(Service(id=s.id, asset_id=s.asset_id, port=s.port, protocol=s.protocol, name=s.name, state=s.state))

            vulns = await session.execute(select(DBVulnerability))
            for v in vulns.scalars():
                self.graph.add_node(v.id, type="vulnerability", label=v.cve_id or "VULN", severity=v.severity)
                # Implicit relationship: Service HAS Vulnerability (if service_id is set) or Asset HAS Vulnerability
                if v.service_id:
                    self.graph.add_edge(v.service_id, v.id, type="HAS_VULNERABILITY")
                else:
                    self.graph.add_edge(v.asset_id, v.id, type="HAS_VULNERABILITY")
                entities_for_inference["vulnerabilities"].append(Vulnerability(id=v.id, asset_id=v.asset_id, cve_id=v.cve_id, severity=v.severity, description=v.description))

            creds = await session.execute(select(DBCredential))
            for c in creds.scalars():
                self.graph.add_node(c.id, type="credential", label=c.username, cred_type=c.type)
                if c.asset_id:
                    self.graph.add_edge(c.asset_id, c.id, type="HAS_CREDENTIAL")
                entities_for_inference["credentials"].append(Credential(id=c.id, asset_id=c.asset_id, username=c.username, password=c.password, password_hash=c.password_hash, type=c.type))

            # 2. Load Explicit Relationships
            rels = await session.execute(select(DBRelationship))
            for r in rels.scalars():
                self.graph.add_edge(r.source_id, r.target_id, type=r.type, **(r.metadata_json or {}))

            # 3. Perform Autonomous Inference if requested
            if infer:
                inferred_rels = self.intelligence.infer_relationships(entities_for_inference)
                for ir in inferred_rels:
                    self.graph.add_edge(ir.source_id, ir.target_id, type=ir.type, inferred=True, **ir.metadata)
                
                # Calculate risk scores
                scores = self.intelligence.calculate_risk_scores(entities_for_inference)
                for asset_id, score in scores.items():
                    if asset_id in self.graph:
                        self.graph.nodes[asset_id]["risk_score"] = score

    def find_attack_paths(self, source_id: str, target_id: str) -> List[List[str]]:
        """Finds all simple paths between two nodes."""
        if source_id not in self.graph or target_id not in self.graph:
            return []
        return list(nx.all_simple_paths(self.graph, source=source_id, target=target_id))

    def analyze_critical_paths(self) -> List[Dict[str, Any]]:
        """Identifies high-severity attack paths (e.g., Internet -> Vuln -> Asset)."""
        critical_paths = []
        
        # Sources: Internet or high-risk assets
        sources = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "source"]
        # Targets: Assets with high risk scores
        targets = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "asset" and d.get("risk_score", 0) > 7.0]

        for source in sources:
            for target in targets:
                paths = self.find_attack_paths(source, target)
                for path in paths:
                    # Check if path involves an exploitable vulnerability
                    has_exploit = any(
                        self.graph.get_edge_data(path[i], path[i+1]).get("type") == "EXPLOITABLE_VIA"
                        for i in range(len(path)-1)
                    )
                    
                    if has_exploit:
                        critical_paths.append({
                            "source": source,
                            "target": target,
                            "path": path,
                            "severity": "Critical",
                            "description": "Path from Internet to high-risk asset via exploitable vulnerability."
                        })
        
        return critical_paths

    def get_graph_data(self) -> Dict[str, Any]:
        """Returns the graph data in a format suitable for visualization (D3.js)."""
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **attrs})
        
        links = []
        for u, v, attrs in self.graph.edges(data=True):
            links.append({"source": u, "target": v, **attrs})
        
        return {"nodes": nodes, "links": links}
