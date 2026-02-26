import pytest
from cosf.engine.intelligence import InferenceEngine, CredentialReuseRule, ServiceMatchingRule
from cosf.models.som import Asset, Service, Credential

def test_credential_reuse_rule():
    rule = CredentialReuseRule()
    
    cred1 = Credential(asset_id="asset-A", username="admin", password="password123")
    cred2 = Credential(asset_id="asset-B", username="admin", password="password123")
    cred3 = Credential(asset_id="asset-C", username="user", password="password123")
    
    rels = rule.apply({"credentials": [cred1, cred2, cred3]})
    
    assert len(rels) == 1
    rel = rels[0]
    assert rel.type == "CREDENTIAL_REUSE"
    assert {rel.source_id, rel.target_id} == {"asset-A", "asset-B"}

def test_service_matching_rule():
    rule = ServiceMatchingRule()
    
    s1 = Service(asset_id="asset-1", port=22, protocol="tcp", name="ssh")
    s2 = Service(asset_id="asset-2", port=22, protocol="tcp", name="ssh")
    s3 = Service(asset_id="asset-3", port=80, protocol="tcp", name="http")
    
    rels = rule.apply({"services": [s1, s2, s3]})
    
    assert len(rels) == 1
    assert rels[0].type == "SAME_SERVICE"
    assert {rels[0].source_id, rels[0].target_id} == {"asset-1", "asset-2"}

def test_inference_engine_integration():
    engine = InferenceEngine()
    
    cred1 = Credential(asset_id="A", username="u", password="p")
    cred2 = Credential(asset_id="B", username="u", password="p")
    s1 = Service(asset_id="A", port=80, protocol="tcp", name="h")
    s2 = Service(asset_id="B", port=80, protocol="tcp", name="h")
    
    entities = {
        "credentials": [cred1, cred2],
        "services": [s1, s2]
    }
    
    rels = engine.infer_relationships(entities)
    assert len(rels) == 2
    types = [r.type for r in rels]
    assert "CREDENTIAL_REUSE" in types
    assert "SAME_SERVICE" in types
