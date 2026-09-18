import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("authorized_targets.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    original_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_tool: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cve: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cwe: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cvss_vector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    affected_resource: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity_overridden: Mapped[bool] = mapped_column(default=False)
    severity_override_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_detected: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_detected: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")
    target: Mapped["AuthorizedTarget"] = relationship("AuthorizedTarget")
    status_history: Mapped[list["FindingStatusHistory"]] = relationship(
        "FindingStatusHistory", back_populates="finding", cascade="all, delete-orphan"
    )
    remediation_notes: Mapped[list["RemediationNote"]] = relationship(
        "RemediationNote", back_populates="finding", cascade="all, delete-orphan"
    )
    retests: Mapped[list["Retest"]] = relationship("Retest", back_populates="finding")


class FindingStatusHistory(Base):
    __tablename__ = "finding_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    finding_id: Mapped[str] = mapped_column(String(36), ForeignKey("findings.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    finding: Mapped["Finding"] = relationship("Finding", back_populates="status_history")
