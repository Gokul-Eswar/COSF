import networkx as nx
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from cosf.models.database import DBAsset, DBService, DBVulnerability, DBCredential, DBRelationship
from cosf.models.db_session import AsyncSessionLocal

class GraphEngine:
    """Engine for building and analyzing security relationship graphs."""

    def __init__(self):
        self.graph = nx.DiGraph()

    async def build_from_db(self):
        """Builds the graph by fetching all relevant entities and relationships from the DB."""
        self.graph.clear()
        
        async with AsyncSessionLocal() as session:
            # 1. Load Nodes
            assets = await session.execute(select(DBAsset))
            for a in assets.scalars():
                self.graph.add_node(a.id, type="asset", label=a.name, ip=a.ip_address, os=a.os)

            services = await session.execute(select(DBService))
            for s in services.scalars():
                self.graph.add_node(s.id, type="service", label=f"{s.protocol}/{s.port}", name=s.name)
                # Implicit relationship: Asset HAS Service
                self.graph.add_edge(s.asset_id, s.id, type="HAS_SERVICE")

            vulns = await session.execute(select(DBVulnerability))
            for v in vulns.scalars():
                self.graph.add_node(v.id, type="vulnerability", label=v.cve_id or "VULN", severity=v.severity)
                # Implicit relationship: Service HAS Vulnerability (if service_id is set) or Asset HAS Vulnerability
                if v.service_id:
                    self.graph.add_edge(v.service_id, v.id, type="HAS_VULNERABILITY")
                else:
                    self.graph.add_edge(v.asset_id, v.id, type="HAS_VULNERABILITY")

            creds = await session.execute(select(DBCredential))
            for c in creds.scalars():
                self.graph.add_node(c.id, type="credential", label=c.username, cred_type=c.type)
                if c.asset_id:
                    self.graph.add_edge(c.asset_id, c.id, type="HAS_CREDENTIAL")

            # 2. Load Explicit Relationships
            rels = await session.execute(select(DBRelationship))
            for r in rels.scalars():
                self.graph.add_edge(r.source_id, r.target_id, type=r.type, **(r.metadata_json or {}))

    def find_attack_paths(self, source_id: str, target_id: str) -> List[List[str]]:
        """Finds all simple paths between two nodes."""
        if source_id not in self.graph or target_id not in self.graph:
            return []
        return list(nx.all_simple_paths(self.graph, source=source_id, target=target_id))

    def get_graph_data(self) -> Dict[str, Any]:
        """Returns the graph data in a format suitable for visualization (D3.js)."""
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **attrs})
        
        links = []
        for u, v, attrs in self.graph.edges(data=True):
            links.append({"source": u, "target": v, **attrs})
        
        return {"nodes": nodes, "links": links}

    def analyze_critical_paths(self) -> List[Dict[str, Any]]:
        """Identifies high-severity attack paths (e.g., Internet -> Vuln -> Asset)."""
        # This is a placeholder for more complex logic
        # For now, let's just find paths from any asset to any other asset that involve a vulnerability
        paths = []
        # Implement advanced logic as needed
        return paths
