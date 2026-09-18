from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReportCreate(BaseModel):
    executive_summary: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    scan_id: str
    generated_by: str
    version: int
    file_path: Optional[str]
    executive_summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class RetestCreate(BaseModel):
    result_summary: Optional[str] = None
    still_vulnerable: Optional[bool] = None


class RetestRequest(BaseModel):
    pass


class RetestResponse(BaseModel):
    id: str
    finding_id: str
    scan_id: Optional[str]
    requested_by: str
    status: str
    still_vulnerable: Optional[bool]
    result_summary: Optional[str]
    confirmed_by: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RetestComplete(BaseModel):
    still_vulnerable: bool
    result_summary: str
    confirmed_by: Optional[str] = None


class ScanCompareResult(BaseModel):
    scan_a_id: str
    scan_b_id: str
    new_findings: list
    resolved_findings: list
    persisting_findings: list
    summary: dict
