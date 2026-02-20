import pytest
from pydantic import ValidationError
from cosf.models.som import Asset, Service, Vulnerability

def test_asset_creation():
    asset = Asset(id="asset-1", name="Test Asset", ip_address="192.168.1.1")
    assert asset.id == "asset-1"
    assert asset.name == "Test Asset"
    assert str(asset.ip_address) == "192.168.1.1"

def test_service_creation():
    service = Service(id="service-1", asset_id="asset-1", port=80, protocol="tcp", name="http")
    assert service.port == 80
    assert service.protocol == "tcp"

def test_vulnerability_creation():
    vuln = Vulnerability(
        id="vuln-1",
        asset_id="asset-1",
        cve_id="CVE-2021-1234",
        severity="high",
        description="A test vulnerability"
    )
    assert vuln.severity == "high"
    assert vuln.cve_id == "CVE-2021-1234"

def test_asset_invalid_ip():
    with pytest.raises(ValidationError):
        Asset(id="asset-1", name="Test Asset", ip_address="invalid-ip")
