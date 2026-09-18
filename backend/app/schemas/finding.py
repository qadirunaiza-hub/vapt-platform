from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


SEVERITY_LEVELS = ["critical", "high", "medium", "low", "informational"]
FINDING_STATUSES = ["open", "assigned", "in_progress", "fixed", "retest_required", "closed", "false_positive"]


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    target_id: str
    title: str
    description: Optional[str]
    severity: str
    original_severity: Optional[str]
    confidence: Optional[str]
    source_tool: str
    category: Optional[str]
    cve: Optional[str]
    cwe: Optional[str]
    cvss_score: Optional[float]
    cvss_vector: Optional[str]
    affected_resource: Optional[str]
    evidence: Optional[str]
    impact: Optional[str]
    recommendation: Optional[str]
    status: str
    assigned_to: Optional[str]
    severity_overridden: bool
    severity_override_justification: Optional[str]
    first_detected: datetime
    last_detected: datetime

    model_config = {"from_attributes": True}


class FindingUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    severity: Optional[str] = None
    severity_override_justification: Optional[str] = None


class RemediationNoteCreate(BaseModel):
    note: str


class RemediationNoteResponse(BaseModel):
    id: str
    finding_id: str
    author: str
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusHistoryResponse(BaseModel):
    id: str
    previous_status: Optional[str]
    new_status: str
    changed_by: str
    comment: Optional[str]
    changed_at: datetime

    model_config = {"from_attributes": True}
