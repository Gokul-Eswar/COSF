import math
import logging
from typing import List, Dict, Any, Tuple
import networkx as nx
from cosf.engine.graph import GraphEngine

logger = logging.getLogger(__name__)

class PredictiveAttackEngine:
    """Engine for predicting attacker paths and next-hop moves in the security graph."""

    def __init__(self, graph_engine: GraphEngine):
        self.graph_engine = graph_engine
        self.graph = graph_engine.graph

    def calculate_transition_probability(self, u: str, v: str, edge_attrs: Dict[str, Any]) -> float:
        """Calculates the probability of an attacker transitioning from node u to node v."""
        # 1. Base probability based on edge type
        rel_type = edge_attrs.get("type", "").upper()
        
        if "EXPLOITABLE_VIA" in rel_type:
            base_prob = 0.90
        elif "CREDENTIAL_REUSE" in rel_type:
            base_prob = 0.85
        elif "HAS_SERVICE" in rel_type or "SERVICE_VULNERABILITY" in rel_type:
            base_prob = 0.60
        elif "ACCESSIBLE_FROM" in rel_type or "EXTERNAL_VISIBILITY" in rel_type:
            base_prob = 0.55
        elif "NETWORK_PROXIMITY" in rel_type:
            base_prob = 0.45
        elif "SAME_SERVICE" in rel_type:
            base_prob = 0.35
        else:
            base_prob = 0.20

        # 2. Modify based on target node attributes
        target_attrs = self.graph.nodes.get(v, {})
        target_type = target_attrs.get("type", "")

        prob = base_prob

        if target_type == "vulnerability":
            severity = target_attrs.get("severity", "").lower()
            if severity == "critical":
                prob *= 1.3
            elif severity == "high":
                prob *= 1.15
            elif severity == "medium":
                prob *= 1.0
            elif severity == "low":
                prob *= 0.8
        elif target_type == "asset":
            # Attacker is drawn to high-value/high-risk assets
            risk_score = target_attrs.get("risk_score", 1.0)
            prob *= (0.8 + (risk_score / 10.0) * 0.4) # scale between 0.8 and 1.2

        # 3. Centrality modifier (attacker pivots to nodes with high centrality)
        out_degree = self.graph.out_degree(v) if self.graph.has_node(v) else 0
        centrality_boost = min(out_degree * 0.05, 0.2)
        prob += centrality_boost

        # Cap probability in valid bounds
        return max(0.01, min(0.99, prob))

    def predict_next_moves(self, current_node: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Predicts the next most likely nodes an attacker would target from the current node."""
        if not self.graph.has_node(current_node):
            return []

        predictions = []
        for neighbor in self.graph.neighbors(current_node):
            edge_data = self.graph.get_edge_data(current_node, neighbor)
            prob = self.calculate_transition_probability(current_node, neighbor, edge_data)
            
            target_attrs = self.graph.nodes.get(neighbor, {})
            
            predictions.append({
                "target_node": neighbor,
                "target_type": target_attrs.get("type", "unknown"),
                "target_label": target_attrs.get("label", neighbor),
                "relationship_type": edge_data.get("type", "RELATED_TO"),
                "probability": prob
            })

        # Sort by probability descending
        predictions.sort(key=lambda x: x["probability"], reverse=True)
        return predictions[:top_n]

    def predict_attack_paths(self, source_id: str, target_id: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """Predicts the most likely attack paths between a source and a target node."""
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return []

        # Create a weighted graph where edge weight is -log(probability)
        # This converts path probability multiplication into distance addition (Dijkstra)
        weighted_graph = nx.DiGraph()
        
        for node_id, attrs in self.graph.nodes(data=True):
            weighted_graph.add_node(node_id, **attrs)

        for u, v, attrs in self.graph.edges(data=True):
            prob = self.calculate_transition_probability(u, v, attrs)
            weight = -math.log(prob)
            weighted_graph.add_edge(u, v, weight=weight, probability=prob)

        try:
            # Find the N shortest paths in the weighted graph
            paths = list(nx.shortest_simple_paths(weighted_graph, source=source_id, target=target_id, weight="weight"))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

        predicted_paths = []
        for path in paths[:top_n]:
            # Calculate overall path probability
            path_prob = 1.0
            steps = []
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                edge_data = weighted_graph.get_edge_data(u, v)
                prob = edge_data["probability"]
                path_prob *= prob
                
                u_label = self.graph.nodes[u].get("label", u)
                v_label = self.graph.nodes[v].get("label", v)
                rel_type = self.graph.get_edge_data(u, v).get("type", "RELATED_TO")
                
                # Make step description human readable
                if "EXPLOITABLE_VIA" in rel_type:
                    desc = f"Exploit vulnerability on '{u_label}' targeting '{v_label}'"
                elif "CREDENTIAL_REUSE" in rel_type:
                    desc = f"Pivot from '{u_label}' to '{v_label}' via reused credentials"
                elif "NETWORK_PROXIMITY" in rel_type:
                    desc = f"Scan/pivot from '{u_label}' to '{v_label}' due to network proximity"
                elif "HAS_SERVICE" in rel_type:
                    desc = f"Locate service '{v_label}' running on asset '{u_label}'"
                elif "ACCESSIBLE_FROM" in rel_type:
                    desc = f"Access service '{v_label}' externally from '{u_label}'"
                else:
                    desc = f"Move from '{u_label}' to '{v_label}' via relationship type '{rel_type}'"
                
                steps.append({
                    "from_node": u,
                    "to_node": v,
                    "description": desc,
                    "probability": prob
                })

            predicted_paths.append({
                "path": path,
                "probability": path_prob,
                "steps": steps
            })

        return predicted_paths

    def analyze_highest_risk_paths(self) -> List[Dict[str, Any]]:
        """Predicts high-likelihood attack paths from the Internet to any high-risk assets."""
        sources = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "source"]
        targets = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "asset" and d.get("risk_score", 0) > 6.0]

        high_risk_paths = []
        for src in sources:
            for tgt in targets:
                paths = self.predict_attack_paths(src, tgt, top_n=2)
                for p in paths:
                    # Only include paths with reasonable probability (e.g. > 1%)
                    if p["probability"] > 0.01:
                        high_risk_paths.append({
                            "source": src,
                            "target": tgt,
                            "target_label": self.graph.nodes[tgt].get("label", tgt),
                            "target_risk_score": self.graph.nodes[tgt].get("risk_score", 0),
                            "path": p["path"],
                            "probability": p["probability"],
                            "steps": p["steps"]
                        })

        # Sort by path probability descending
        high_risk_paths.sort(key=lambda x: x["probability"], reverse=True)
        return high_risk_paths
