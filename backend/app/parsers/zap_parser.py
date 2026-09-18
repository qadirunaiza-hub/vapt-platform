"""
Parse OWASP ZAP JSON report output into normalized findings.
ZAP risk levels: 3=High, 2=Medium, 1=Low, 0=Informational
"""
import json
from typing import List
from app.parsers.base import BaseParser, NormalizedFinding, normalize_severity


_ZAP_RISK_MAP = {"3": "high", "2": "medium", "1": "low", "0": "informational"}
_ZAP_CONF_MAP = {"3": "high", "2": "medium", "1": "low", "0": "false_positive"}


class ZAPParser(BaseParser):
    def parse(self, raw_output: str) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, ValueError):
            return findings

        sites = data.get("site", [])
        if isinstance(sites, dict):
            sites = [sites]

        for site in sites:
            alerts = site.get("alerts", [])
            for alert in alerts:
                risk_code = str(alert.get("riskcode", "0"))
                conf_code = str(alert.get("confidence", "1"))
                severity = _ZAP_RISK_MAP.get(risk_code, "informational")
                confidence = _ZAP_CONF_MAP.get(conf_code, "medium")

                instances = alert.get("instances", [])
                affected = alert.get("url", "")
                if instances:
                    affected = instances[0].get("uri", affected)

                cwe_id = alert.get("cweid", "")
                cwe = f"CWE-{cwe_id}" if cwe_id and cwe_id != "0" else ""

                findings.append(NormalizedFinding(
                    title=alert.get("alert", "Unknown ZAP Alert"),
                    severity=severity,
                    original_severity=alert.get("riskdesc", severity),
                    confidence=confidence,
                    source_tool="zap",
                    affected_resource=affected,
                    description=alert.get("desc", ""),
                    evidence=alert.get("evidence", ""),
                    impact=alert.get("riskdesc", ""),
                    recommendation=alert.get("solution", ""),
                    category="web",
                    cwe=cwe,
                    raw_data=alert,
                ))

        return findings
