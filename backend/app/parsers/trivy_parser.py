"""
Parse Trivy JSON output into normalized findings.
Handles vulnerability, secret, and misconfiguration result types.
"""
import json
from typing import List
from app.parsers.base import BaseParser, NormalizedFinding, normalize_severity


class TrivyParser(BaseParser):
    def parse(self, raw_output: str) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, ValueError):
            return findings

        results = data.get("Results", [])
        for result in results:
            target = result.get("Target", "")
            result_type = result.get("Type", "")

            for vuln in result.get("Vulnerabilities", []):
                cve = vuln.get("VulnerabilityID", "")
                pkg = vuln.get("PkgName", "")
                installed = vuln.get("InstalledVersion", "")
                fixed = vuln.get("FixedVersion", "")
                severity = normalize_severity(vuln.get("Severity", "unknown"))
                cvss_score = None
                cvss_vector = ""
                cvss_data = vuln.get("CVSS", {})
                for source_data in cvss_data.values():
                    if isinstance(source_data, dict):
                        cvss_score = source_data.get("V3Score") or source_data.get("V2Score")
                        cvss_vector = source_data.get("V3Vector", "") or source_data.get("V2Vector", "")
                        break

                title = f"{cve} in {pkg}" if cve else f"Vulnerability in {pkg}"
                description = vuln.get("Description", "")
                fix_note = f"\nFixed in version: {fixed}" if fixed else "\nNo fix available at time of scan."

                findings.append(NormalizedFinding(
                    title=title,
                    severity=severity,
                    original_severity=vuln.get("Severity", severity),
                    source_tool="trivy",
                    affected_resource=f"{target} → {pkg}@{installed}",
                    description=description + fix_note,
                    recommendation=f"Upgrade {pkg} to {fixed}" if fixed else "Monitor for available fix.",
                    category=f"dependency ({result_type})",
                    cve=cve,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    confidence="high",
                    raw_data=vuln,
                ))

            for secret in result.get("Secrets", []):
                findings.append(NormalizedFinding(
                    title=f"Secret detected: {secret.get('Title', 'Unknown secret')}",
                    severity="high",
                    original_severity="HIGH",
                    source_tool="trivy",
                    affected_resource=f"{target}:{secret.get('StartLine', '?')}",
                    description=secret.get("Match", ""),
                    evidence=secret.get("Match", ""),
                    recommendation="Rotate the secret immediately. Remove from source and use a secrets manager.",
                    category="secret",
                    confidence="high",
                    raw_data=secret,
                ))

            for misconfig in result.get("Misconfigurations", []):
                severity = normalize_severity(misconfig.get("Severity", "unknown"))
                findings.append(NormalizedFinding(
                    title=misconfig.get("Title", "Misconfiguration"),
                    severity=severity,
                    original_severity=misconfig.get("Severity", severity),
                    source_tool="trivy",
                    affected_resource=target,
                    description=misconfig.get("Description", ""),
                    recommendation=misconfig.get("Resolution", ""),
                    category="misconfiguration",
                    confidence="high",
                    raw_data=misconfig,
                ))

        return findings
