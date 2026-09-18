from datetime import datetime
from typing import Optional
from pydantic import BaseModel


TARGET_TYPES = ["web_application", "api", "host_ip", "docker_image", "kubernetes", "source_repository"]
ENVIRONMENTS = ["development", "staging", "production", "internal"]


class TargetCreate(BaseModel):
    name: str
    target_type: str
    address: str
    environment: str = "development"
    owner: str
    description: Optional[str] = None
    authorization_confirmed: bool
    authorization_note: Optional[str] = None

    def model_post_init(self, __context):
        self.address = self.address.strip()


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    environment: Optional[str] = None
    is_active: Optional[bool] = None


class TargetResponse(BaseModel):
    id: str
    name: str
    target_type: str
    address: str
    environment: str
    owner: str
    description: Optional[str]
    authorization_confirmed: bool
    authorization_note: Optional[str]
    is_active: bool
    created_by: str
    created_at: datetime
    last_scanned_at: Optional[datetime]

    model_config = {"from_attributes": True}
