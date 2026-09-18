from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class NormalizedFinding:
    title: str
    severity: str
    source_tool: str
    affected_resource: str = ""
    description: str = ""
    evidence: str = ""
    impact: str = ""
    recommendation: str = ""
    category: str = ""
    cve: str = ""
    cwe: str = ""
    cvss_score: Optional[float] = None
    cvss_vector: str = ""
    confidence: str = "medium"
    original_severity: str = ""
    raw_data: dict = field(default_factory=dict)


SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "informational",
    "informational": "informational",
    # ZAP numeric risk codes
    "3": "high",
    "2": "medium",
    "1": "low",
    "0": "informational",
    # Trivy extras
    "unknown": "informational",
    "negligible": "informational",
}


def normalize_severity(raw: str) -> str:
    return SEVERITY_MAP.get(raw.lower().strip(), "informational")


class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_output: str) -> List[NormalizedFinding]:
        """Parse raw tool output and return normalized findings."""
