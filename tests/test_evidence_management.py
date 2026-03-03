import pytest
import os
import shutil
from cosf.models.evidence import EvidenceManager
from cosf.utils.crypto import CryptoManager
from cosf.models.som import Evidence

def test_evidence_manager_store():
    # Setup temp storage
    storage = "test_evidence_dir"
    if os.path.exists(storage):
        shutil.rmtree(storage)
    
    from cosf.utils.storage import LocalStorageProvider
    manager = EvidenceManager(storage=LocalStorageProvider(storage_path=storage))
    data = b"fake pcap data content"
    
    evidence = manager.store_artifact(
        name="test_capture",
        artifact_type="pcap",
        data=data,
        task_id="task-123",
        metadata={"interface": "eth0"}
    )
    
    assert isinstance(evidence, Evidence)
    assert evidence.name == "test_capture"
    assert evidence.type == "pcap"
    assert os.path.exists(evidence.file_path)
    assert evidence.hash_sha256 == "dcd2b28b6c53b8387c06189c00a95d321fd2f175a8dc08e673b5851b4631eb74"
    
    # Cleanup
    shutil.rmtree(storage)

def test_crypto_manager_sign_verify():
    priv, pub = CryptoManager.generate_key_pair()
    message = "test message 123"
    
    signature = CryptoManager.sign_message(priv, message)
    assert signature is not None
    
    # Valid verification
    assert CryptoManager.verify_signature(pub, message, signature) is True
    
    # Invalid message
    assert CryptoManager.verify_signature(pub, "wrong message", signature) is False
    
    # Invalid signature
    assert CryptoManager.verify_signature(pub, message, "bm90IGEgc2lnbmF0dXJl") is False

def test_verification_logic_with_tampering():
    priv, pub = CryptoManager.generate_key_pair()
    original_output = "Nmap scan results: 2 ports open"
    signature = CryptoManager.sign_message(priv, f"task-123:{original_output}")
    
    # Validation succeeds with original data
    assert CryptoManager.verify_signature(pub, f"task-123:{original_output}", signature) is True
    
    # Validation fails if output is tampered
    tampered_output = "Nmap scan results: 0 ports open"
    assert CryptoManager.verify_signature(pub, f"task-123:{tampered_output}", signature) is False
