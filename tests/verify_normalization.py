import asyncio
import json
from cosf.engine.normalization import NmapNormalizer, NucleiNormalizer, FingerprintRule

def test_nmap_normalization():
    print("Testing Nmap normalization...")
    raw_nmap = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun>
  <host>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <hostnames><hostname name="gateway.local" type="user"/></hostnames>
    <ports>
      <port protocol="tcp" portid="80"><state state="open"/><service name="http" product="Apache httpd" version="2.4.41 (Ubuntu)"/></port>
    </ports>
    <os><osmatch name="Linux 5.4" accuracy="100"/></os>
  </host>
</nmaprun>"""
    
    normalizer = NmapNormalizer()
    entities = normalizer.normalize(raw_nmap)
    
    # Check Asset
    asset = next(e for e in entities if hasattr(e, "ip_address"))
    print(f"  Asset: {asset.name} ({asset.ip_address}), OS: {asset.os}")
    assert str(asset.ip_address) == "192.168.1.1"
    assert asset.os == "Linux" # FingerprintRule should normalize "Linux 5.4" to "Linux"
    
    # Check Service
    service = next(e for e in entities if hasattr(e, "port"))
    print(f"  Service: {service.name} on {service.port}, Product: {service.product}, Version: {service.version}")
    assert service.port == 80
    assert service.version == "2.4.41" # FingerprintRule should strip "(Ubuntu)"
    
    print("Nmap normalization test passed!")

def test_nuclei_normalization():
    print("Testing Nuclei normalization...")
    raw_nuclei = """{"template-id":"cve-2021-44228","info":{"name":"Apache Log4j2 Remote Code Execution","severity":"critical"},"ip":"1.2.3.4","matched-at":"http://1.2.3.4:8080"}"""
    
    normalizer = NucleiNormalizer()
    entities = normalizer.normalize(raw_nuclei)
    
    vuln = next(e for e in entities if hasattr(e, "cve_id"))
    print(f"  Vulnerability: {vuln.cve_id}, Severity: {vuln.severity}")
    assert vuln.cve_id == "cve-2021-44228"
    assert vuln.severity == "Critical" # SeverityMapper should normalize "critical" to "Critical"
    
    print("Nuclei normalization test passed!")

if __name__ == "__main__":
    test_nmap_normalization()
    test_nuclei_normalization()
