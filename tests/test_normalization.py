import pytest
from cosf.engine.normalization import NormalizationEngine, SeverityMapper
from cosf.models.som import Asset, Service, Vulnerability

def test_severity_mapper():
    assert SeverityMapper.normalize("critical") == "Critical"
    assert SeverityMapper.normalize("fatal") == "Critical"
    assert SeverityMapper.normalize("unknown") == "Unknown"
    assert SeverityMapper.normalize("info") == "Info"

def test_nmap_normalization():
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <nmaprun>
      <host>
        <address addr="192.168.1.1" addrtype="ipv4"/>
        <hostnames><hostname name="test-host"/></hostnames>
        <ports>
          <port protocol="tcp" portid="80"><state state="open"/><service name="http"/></port>
        </ports>
      </host>
    </nmaprun>"""
    
    entities = NormalizationEngine.normalize_output("nmap", mock_xml)
    assert len(entities) == 2
    asset = next(e for e in entities if isinstance(e, Asset))
    service = next(e for e in entities if isinstance(e, Service))
    
    assert str(asset.ip_address) == "192.168.1.1"
    assert asset.name == "test-host"
    assert service.port == 80
    assert service.protocol == "tcp"

def test_nuclei_normalization():
    mock_json = '{"template-id":"test-vuln","info":{"severity":"high","name":"Test Vulnerability"},"ip":"1.1.1.1","matched-at":"http://1.1.1.1"}'
    
    entities = NormalizationEngine.normalize_output("nuclei", mock_json)
    assert len(entities) == 1
    vuln = entities[0]
    assert isinstance(vuln, Vulnerability)
    assert vuln.severity == "High"
    assert vuln.cve_id == "test-vuln"
    assert "Test Vulnerability" in vuln.description

def test_nmap_normalization_with_fingerprints():
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <nmaprun>
      <host>
        <address addr="10.0.0.5" addrtype="ipv4"/>
        <os><osmatch name="Linux 4.15 - 5.6" accuracy="100"/></os>
        <ports>
          <port protocol="tcp" portid="22">
            <state state="open"/>
            <service name="ssh" product="OpenSSH" version="8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)"/>
          </port>
        </ports>
      </host>
    </nmaprun>"""
    
    entities = NormalizationEngine.normalize_output("nmap", mock_xml)
    asset = next(e for e in entities if isinstance(e, Asset))
    service = next(e for e in entities if isinstance(e, Service))
    
    assert asset.os == "Linux"
    assert service.product == "OpenSSH"
    assert service.version == "8.2p1 Ubuntu 4ubuntu0.1"

def test_unsupported_tool():
    entities = NormalizationEngine.normalize_output("unknown_tool", "some output")
    assert entities == []
