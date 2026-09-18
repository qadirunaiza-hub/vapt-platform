from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


SCAN_PROFILES = ["quick_scan", "web_api_scan", "network_scan", "container_scan", "full_vapt"]
SCAN_TOOLS = ["nmap", "zap", "trivy", "semgrep"]
SCAN_INTENSITIES = ["passive", "normal", "aggressive"]


class ScanCreate(BaseModel):
    target_id: str
    scan_profile: str
    tools: List[str]
    intensity: str = "normal"
    scan_options: Dict[str, Any] = {}


class ScanJobResponse(BaseModel):
    id: str
    tool: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    findings_count: int
    retry_count: int

    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    id: str
    target_id: str
    created_by: str
    scan_profile: str
    tools: List[str]
    intensity: str
    status: str
    progress: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    error_message: Optional[str]
    scan_options: Dict[str, Any]
    jobs: List[ScanJobResponse] = []

    model_config = {"from_attributes": True}


class ScanSummary(BaseModel):
    id: str
    target_id: str
    target_name: str
    scan_profile: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0

    model_config = {"from_attributes": True}
