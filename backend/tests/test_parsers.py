from app.parsers.nmap_parser import NmapParser
from app.parsers.zap_parser import ZAPParser
from app.parsers.trivy_parser import TrivyParser

NMAP_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <hostnames><hostname name="router.local" type="PTR"/></hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.9"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="nginx" version="1.24"/>
      </port>
      <port protocol="tcp" portid="23">
        <state state="open"/>
        <service name="telnet"/>
      </port>
    </ports>
  </host>
</nmaprun>"""

ZAP_JSON = """{
  "site": [{
    "alerts": [
      {
        "alert": "Missing Content-Security-Policy Header",
        "riskcode": "2",
        "confidence": "2",
        "desc": "CSP not set",
        "solution": "Add a CSP header",
        "url": "https://example.com",
        "cweid": "16",
        "evidence": ""
      }
    ]
  }]
}"""

TRIVY_JSON = """{
  "Results": [
    {
      "Target": "nginx:latest",
      "Type": "debian",
      "Vulnerabilities": [
        {
          "VulnerabilityID": "CVE-2023-1234",
          "PkgName": "libssl",
          "InstalledVersion": "1.1.1",
          "FixedVersion": "1.1.2",
          "Severity": "HIGH",
          "Description": "SSL vulnerability"
        }
      ]
    }
  ]
}"""


def test_nmap_parser():
    parser = NmapParser()
    findings = parser.parse(NMAP_XML)
    assert len(findings) >= 3
    titles = [f.title for f in findings]
    assert any("22" in t for t in titles)
    telnet = next((f for f in findings if "23" in f.title), None)
    assert telnet is not None
    assert telnet.severity == "high"


def test_zap_parser():
    parser = ZAPParser()
    findings = parser.parse(ZAP_JSON)
    assert len(findings) == 1
    assert findings[0].severity == "medium"
    assert findings[0].cwe == "CWE-16"


def test_trivy_parser():
    parser = TrivyParser()
    findings = parser.parse(TRIVY_JSON)
    assert len(findings) == 1
    assert findings[0].cve == "CVE-2023-1234"
    assert findings[0].severity == "high"
    assert "1.1.2" in findings[0].description


def test_nmap_parser_empty():
    parser = NmapParser()
    assert parser.parse("") == []
    assert parser.parse("<invalid>") == []


def test_zap_parser_invalid():
    parser = ZAPParser()
    assert parser.parse("not json") == []
