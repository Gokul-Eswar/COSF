import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from cosf.engine.graph import GraphEngine
from cosf.models.database import DBAsset, DBService, DBVulnerability, DBRelationship

@pytest.mark.asyncio
@patch("cosf.engine.graph.AsyncSessionLocal")
async def test_graph_build_from_db(mock_session_local):
    # Setup mocks
    mock_session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session
    
    # Mock database data
    mock_asset = DBAsset(id="asset-1", name="Test Asset", ip_address="192.168.1.1")
    mock_service = DBService(id="service-1", asset_id="asset-1", port=80, protocol="tcp", name="http")
    mock_vuln = DBVulnerability(id="vuln-1", asset_id="asset-1", service_id="service-1", cve_id="CVE-2023-1234", severity="high")
    mock_rel = DBRelationship(id="rel-1", source_id="asset-1", target_id="asset-2", type="ACCESSIBLE_VIA")
    
    # Mock scalars().all() or iterating over the result
    class MockResult:
        def __init__(self, data):
            self.data = data
        def scalars(self):
            return self
        def __iter__(self):
            return iter(self.data)

    mock_session.execute.side_effect = [
        MockResult([mock_asset]),
        MockResult([mock_service]),
        MockResult([mock_vuln]),
        MockResult([]), # creds
        MockResult([mock_rel])
    ]
    
    engine = GraphEngine()
    await engine.build_from_db()
    
    # Verify nodes
    assert engine.graph.has_node("asset-1")
    assert engine.graph.has_node("service-1")
    assert engine.graph.has_node("vuln-1")
    assert engine.graph.nodes["asset-1"]["type"] == "asset"
    
    # Verify edges
    assert engine.graph.has_edge("asset-1", "service-1") # Implicit HAS_SERVICE
    assert engine.graph.has_edge("service-1", "vuln-1") # Implicit HAS_VULNERABILITY
    assert engine.graph.has_edge("asset-1", "asset-2")   # Explicit Relationship

def test_graph_find_attack_paths():
    engine = GraphEngine()
    engine.graph.add_edge("A", "B")
    engine.graph.add_edge("B", "C")
    engine.graph.add_edge("C", "D")
    engine.graph.add_edge("A", "X")
    engine.graph.add_edge("X", "D")
    
    paths = engine.find_attack_paths("A", "D")
    assert ["A", "B", "C", "D"] in paths
    assert ["A", "X", "D"] in paths
    assert len(paths) == 2
