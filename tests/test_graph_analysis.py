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
    mock_vuln = DBVulnerability(id="vuln-1", asset_id="asset-1", service_id="service-1", cve_id="CVE-2023-1234", severity="high", description="Test vulnerability")
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

@pytest.mark.asyncio
async def test_graph_find_attack_paths():
    engine = GraphEngine()
    engine.graph.add_edge("A", "B")
    engine.graph.add_edge("B", "C")
    engine.graph.add_edge("C", "D")
    engine.graph.add_edge("A", "X")
    engine.graph.add_edge("X", "D")
    
    paths = await engine.find_attack_paths("A", "D")
    assert ["A", "B", "C", "D"] in paths
    assert ["A", "X", "D"] in paths
    assert len(paths) == 2

@pytest.mark.asyncio
async def test_neo4j_integration_mocked():
    # Mock Neo4j driver and session
    mock_session = AsyncMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    with patch("cosf.engine.graph.NEO4J_URI", "bolt://localhost:7687"), \
         patch("cosf.engine.graph.NEO4J_AVAILABLE", True), \
         patch("cosf.engine.graph.get_neo4j_driver", return_value=mock_driver):
         
        engine = GraphEngine()
        assert engine.use_neo4j is True
        
        # Populate NetworkX graph manually for testing sync
        engine.graph.add_node("asset-1", type="asset", label="Test Asset", risk_score=5.0)
        engine.graph.add_edge("internet", "asset-1", type="ACCESSIBLE_FROM")
        
        await engine.sync_to_neo4j()
        
        # Verify MERGE and MATCH Cypher queries were run
        assert mock_session.run.call_count >= 3
        
        # Mock result for find_attack_paths
        mock_result = AsyncMock()
        mock_record = {"path": ["internet", "asset-1"]}
        mock_result.__aiter__.return_value = iter([mock_record])
        mock_session.run.return_value = mock_result
        
        paths = await engine.find_attack_paths("internet", "asset-1")
        assert paths == [["internet", "asset-1"]]

def test_predictive_attack_engine():
    from cosf.engine.predictive import PredictiveAttackEngine
    engine = GraphEngine()
    
    # Setup a sample graph: Source node (internet) and Asset node
    engine.graph.add_node("internet", type="source", label="Internet")
    engine.graph.add_node("asset-1", type="asset", label="Web Server", risk_score=8.5)
    engine.graph.add_node("service-1", type="service", label="TCP/80", port=80)
    engine.graph.add_node("vuln-1", type="vulnerability", label="CVE-2021-44228", severity="critical")
    engine.graph.add_node("asset-2", type="asset", label="Database", risk_score=9.0)
    
    # Setup relationships
    engine.graph.add_edge("internet", "service-1", type="ACCESSIBLE_FROM")
    engine.graph.add_edge("service-1", "vuln-1", type="HAS_VULNERABILITY")
    engine.graph.add_edge("vuln-1", "exploit/multi/http/log4shell_header_injection", type="EXPLOITABLE_VIA")
    engine.graph.add_edge("exploit/multi/http/log4shell_header_injection", "asset-1", type="EXPLOITS")
    engine.graph.add_edge("asset-1", "asset-2", type="CREDENTIAL_REUSE")
    
    predictive_engine = PredictiveAttackEngine(engine)
    
    # 1. Test next moves
    moves = predictive_engine.predict_next_moves("asset-1")
    assert len(moves) > 0
    assert moves[0]["target_node"] == "asset-2"
    assert moves[0]["relationship_type"] == "CREDENTIAL_REUSE"
    assert moves[0]["probability"] > 0.8
    
    # 2. Test predict attack paths
    paths = predictive_engine.predict_attack_paths("internet", "asset-2", top_n=1)
    assert len(paths) == 1
    path_info = paths[0]
    assert path_info["path"] == ["internet", "service-1", "vuln-1", "exploit/multi/http/log4shell_header_injection", "asset-1", "asset-2"]
    assert path_info["probability"] > 0.0
    assert len(path_info["steps"]) == 5
    
    # 3. Test highest risk paths analysis
    high_risk_paths = predictive_engine.analyze_highest_risk_paths()
    assert len(high_risk_paths) > 0
    targets = [p["target"] for p in high_risk_paths]
    assert "asset-1" in targets
    assert "asset-2" in targets
