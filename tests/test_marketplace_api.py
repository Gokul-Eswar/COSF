import pytest
from unittest.mock import MagicMock
import sys
import asyncio


from fastapi.testclient import TestClient
from cosf.api.main import app
from cosf.models.db_session import init_db

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_database():
    # Run database initialization
    asyncio.run(init_db())
    yield

def test_list_templates():
    response = client.get("/api/marketplace/templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(d["id"] == "recon-basic" for d in data)

def test_get_template_details():
    response = client.get("/api/marketplace/templates/recon-basic")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "recon-basic"
    assert data["name"] == "Basic Reconnaissance"

def test_install_template():
    # Test installing a playbook
    response = client.post("/api/marketplace/templates/recon-basic/install")
    assert response.status_code == 201
    data = response.json()
    assert "draft_id" in data
    assert data["message"] == "Playbook installed as draft"
    
    # Verify the draft exists
    draft_id = data["draft_id"]
    response = client.get(f"/api/drafts/{draft_id}")
    assert response.status_code == 200
    draft_data = response.json()
    assert draft_data["name"] == "Basic Reconnaissance (Installed)"

def test_install_adapter_template():
    import os
    from pathlib import Path
    
    adapter_file = Path("cosf/engine/adapters/ping.py")
    if adapter_file.exists():
        os.remove(adapter_file)
        
    try:
        response = client.post("/api/marketplace/templates/ping/install")
        assert response.status_code == 201
        data = response.json()
        assert data["adapter_id"] == "ping"
        assert "installed successfully" in data["message"]
        
        assert adapter_file.exists()
        code = adapter_file.read_text(encoding="utf-8")
        assert "class PingAdapter" in code
    finally:
        if adapter_file.exists():
            os.remove(adapter_file)

