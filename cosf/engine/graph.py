import networkx as nx
from typing import List, Dict, Any, Optional
import os
import re
import logging
from sqlalchemy import select
from cosf.models.database import DBAsset, DBService, DBVulnerability, DBCredential, DBRelationship
from cosf.models.db_session import AsyncSessionLocal
from cosf.engine.intelligence import InferenceEngine, ExploitMappingRule
from cosf.models.som import Asset, Service, Vulnerability, Credential, Relationship

logger = logging.getLogger(__name__)

try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "cosf-neo4j-password-123")

_neo4j_driver = None

def get_neo4j_driver():
    global _neo4j_driver
    if NEO4J_AVAILABLE and NEO4J_URI and _neo4j_driver is None:
        try:
            _neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception as e:
            logger.warning(f"Failed to create Neo4j driver: {e}")
    return _neo4j_driver

async def close_neo4j_driver():
    global _neo4j_driver
    if _neo4j_driver is not None:
        try:
            await _neo4j_driver.close()
        except Exception as e:
            logger.warning(f"Failed to close Neo4j driver: {e}")
        finally:
            _neo4j_driver = None

class GraphEngine:
    """Engine for building and analyzing security relationship graphs."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.intelligence = InferenceEngine()
        self.driver = get_neo4j_driver()
        self.use_neo4j = self.driver is not None

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

        # Sync to Neo4j if configured
        if self.use_neo4j:
            try:
                await self.sync_to_neo4j()
            except Exception as e:
                logger.warning(f"Failed to sync graph to Neo4j, falling back to local NetworkX query interface. Error: {e}")
                self.use_neo4j = False

    async def sync_to_neo4j(self):
        """Synchronizes the current NetworkX representation to Neo4j."""
        if not self.driver:
            return
        async with self.driver.session() as session:
            # Clear existing data
            await session.run("MATCH (n) DETACH DELETE n")
            
            # Create nodes
            for node_id, attrs in self.graph.nodes(data=True):
                node_type = attrs.get("type", "node")
                # Capitalize label for Neo4j standard (e.g. Asset, Service)
                label = node_type.capitalize()
                
                props = {k: v for k, v in attrs.items() if v is not None}
                props["id"] = node_id
                
                query = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
                await session.run(query, id=node_id, props=props)
                
            # Create edges
            for u, v, attrs in self.graph.edges(data=True):
                rel_type = attrs.get("type", "RELATED_TO")
                sanitized_type = re.sub(r'[^a-zA-Z0-9_]', '', rel_type)
                
                props = {k: v for k, v in attrs.items() if k != "type" and v is not None}
                
                query = (
                    f"MATCH (src {{id: $u}}), (tgt {{id: $v}}) "
                    f"MERGE (src)-[r:{sanitized_type}]->(tgt) "
                    f"SET r += $props"
                )
                await session.run(query, u=u, v=v, props=props)

    async def find_attack_paths(self, source_id: str, target_id: str) -> List[List[str]]:
        """Finds all simple paths between two nodes."""
        if self.use_neo4j:
            try:
                async with self.driver.session() as session:
                    result = await session.run(
                        "MATCH p = (src {id: $source_id})-[*..10]->(tgt {id: $target_id}) "
                        "RETURN [node in nodes(p) | node.id] AS path",
                        source_id=source_id, target_id=target_id
                    )
                    paths = []
                    async for record in result:
                        paths.append(record["path"])
                    return paths
            except Exception as e:
                logger.warning(f"Neo4j query failed: {e}. Falling back to NetworkX.")

        if source_id not in self.graph or target_id not in self.graph:
            return []
        return list(nx.all_simple_paths(self.graph, source=source_id, target=target_id))

    async def analyze_critical_paths(self) -> List[Dict[str, Any]]:
        """Identifies high-severity attack paths (e.g., Internet -> Vuln -> Asset)."""
        if self.use_neo4j:
            try:
                async with self.driver.session() as session:
                    result = await session.run(
                        "MATCH (src) WHERE src.type = 'source' "
                        "MATCH (tgt:Asset) WHERE tgt.risk_score > 7.0 "
                        "MATCH p = (src)-[*..10]->(tgt) "
                        "WHERE any(r in relationships(p) WHERE type(r) = 'EXPLOITABLE_VIA') "
                        "RETURN src.id AS source, tgt.id AS target, [n in nodes(p) | n.id] AS path"
                    )
                    critical_paths = []
                    async for record in result:
                        critical_paths.append({
                            "source": record["source"],
                            "target": record["target"],
                            "path": record["path"],
                            "severity": "Critical",
                            "description": "Path from Internet to high-risk asset via exploitable vulnerability."
                        })
                    return critical_paths
            except Exception as e:
                logger.warning(f"Neo4j query failed: {e}. Falling back to NetworkX.")

        critical_paths = []
        
        # Sources: Internet or high-risk assets
        sources = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "source"]
        # Targets: Assets with high risk scores
        targets = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "asset" and d.get("risk_score", 0) > 7.0]

        for source in sources:
            for target in targets:
                paths = await self.find_attack_paths(source, target)
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

    async def get_graph_data(self) -> Dict[str, Any]:
        """Returns the graph data in a format suitable for visualization (D3.js)."""
        if self.use_neo4j:
            try:
                async with self.driver.session() as session:
                    # Fetch all nodes
                    nodes_res = await session.run("MATCH (n) RETURN n")
                    nodes = []
                    async for record in nodes_res:
                        node = record["n"]
                        node_dict = dict(node)
                        nodes.append(node_dict)
                    
                    # Fetch all relationships
                    rels_res = await session.run(
                        "MATCH (n)-[r]->(m) "
                        "RETURN n.id AS source, m.id AS target, type(r) AS type, properties(r) AS props"
                    )
                    links = []
                    async for record in rels_res:
                        link_dict = {
                            "source": record["source"],
                            "target": record["target"],
                            "type": record["type"],
                            **record["props"]
                        }
                        links.append(link_dict)
                    
                    return {"nodes": nodes, "links": links}
            except Exception as e:
                logger.warning(f"Neo4j query failed: {e}. Falling back to NetworkX.")

        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **attrs})
        
        links = []
        for u, v, attrs in self.graph.edges(data=True):
            links.append({"source": u, "target": v, **attrs})
        
        return {"nodes": nodes, "links": links}
