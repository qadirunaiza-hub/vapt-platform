"""
Parse Nmap XML output (-oX) into normalized findings.
Each open port with service info becomes one finding.
Script output (e.g. vuln scripts) generates additional findings.
"""
import defusedxml.ElementTree as ET
from typing import List
from app.parsers.base import BaseParser, NormalizedFinding


class NmapParser(BaseParser):
    def parse(self, raw_output: str) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        try:
            root = ET.fromstring(raw_output)
        except ET.ParseError:
            return findings

        for host in root.findall("host"):
            address_el = host.find("address[@addrtype='ipv4']")
            if address_el is None:
                address_el = host.find("address[@addrtype='ipv6']")
            if address_el is None:
                continue
            ip = address_el.get("addr", "unknown")

            hostname_el = host.find(".//hostname")
            hostname = hostname_el.get("name", "") if hostname_el is not None else ""
            display_host = f"{hostname} ({ip})" if hostname else ip

            ports_el = host.find("ports")
            if ports_el is None:
                continue

            for port in ports_el.findall("port"):
                state_el = port.find("state")
                if state_el is None or state_el.get("state") != "open":
                    continue

                portid = port.get("portid", "?")
                protocol = port.get("protocol", "tcp")
                service_el = port.find("service")
                service_name = service_el.get("name", "unknown") if service_el is not None else "unknown"
                product = service_el.get("product", "") if service_el is not None else ""
                version = service_el.get("version", "") if service_el is not None else ""
                extrainfo = service_el.get("extrainfo", "") if service_el is not None else ""

                service_detail = " ".join(filter(None, [product, version, extrainfo]))
                title = f"Open port {portid}/{protocol} ({service_name})"
                description = (
                    f"Port {portid}/{protocol} is open on {display_host}.\n"
                    f"Service: {service_name}"
                    + (f" — {service_detail}" if service_detail else "")
                )

                severity = "informational"
                if service_name in ("ftp", "telnet", "rsh", "rlogin", "rexec"):
                    severity = "high"
                    description += "\nWARNING: Cleartext protocol detected."
                elif service_name in ("http",) and portid not in ("80", "8080", "8000"):
                    severity = "low"
                elif service_name in ("rdp", "vnc", "x11"):
                    severity = "medium"

                affected = f"{display_host}:{portid}/{protocol}"

                # Parse NSE script results for vulnerability findings
                for script in port.findall("script"):
                    script_id = script.get("id", "")
                    script_output = script.get("output", "")
                    if "VULNERABLE" in script_output.upper():
                        findings.append(NormalizedFinding(
                            title=f"Nmap Script: {script_id} on {affected}",
                            severity="high",
                            original_severity="high",
                            source_tool="nmap",
                            affected_resource=affected,
                            description=script_output,
                            evidence=script_output,
                            category="network",
                            confidence="medium",
                            raw_data={"script_id": script_id, "output": script_output},
                        ))

                findings.append(NormalizedFinding(
                    title=title,
                    severity=severity,
                    original_severity=severity,
                    source_tool="nmap",
                    affected_resource=affected,
                    description=description,
                    category="network",
                    confidence="high",
                    raw_data={
                        "ip": ip,
                        "hostname": hostname,
                        "port": portid,
                        "protocol": protocol,
                        "service": service_name,
                        "product": product,
                        "version": version,
                    },
                ))

        return findings
