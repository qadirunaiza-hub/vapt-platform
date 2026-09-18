import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("authorized_targets.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    scan_profile: Mapped[str] = mapped_column(String(100), nullable=False)
    tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    intensity: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_options: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    target: Mapped["AuthorizedTarget"] = relationship("AuthorizedTarget", back_populates="scans")
    created_by_user: Mapped["User"] = relationship("User", back_populates="scans", foreign_keys=[created_by])
    jobs: Mapped[list["ScanJob"]] = relationship("ScanJob", back_populates="scan", cascade="all, delete-orphan")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="scan")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="scan")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"), nullable=False)
    tool: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="jobs")
