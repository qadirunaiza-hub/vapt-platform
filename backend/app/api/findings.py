from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.finding import Finding, FindingStatusHistory
from app.models.remediation import RemediationNote
from app.models.audit import AuditLog
from app.schemas.finding import (
    FindingResponse, FindingUpdate, RemediationNoteCreate,
    RemediationNoteResponse, StatusHistoryResponse,
)
from app.api.deps import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=list[FindingResponse])
async def list_findings(
    scan_id: str | None = Query(None),
    target_id: str | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Finding).order_by(Finding.first_detected.desc())
    if scan_id:
        stmt = stmt.where(Finding.scan_id == scan_id)
    if target_id:
        stmt = stmt.where(Finding.target_id == target_id)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
    result = await db.execute(stmt.limit(500))
    return result.scalars().all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    payload: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    previous_status = finding.status
    previous_severity = finding.severity

    if payload.status and payload.status != finding.status:
        finding.status = payload.status
        db.add(FindingStatusHistory(
            finding_id=finding_id,
            previous_status=previous_status,
            new_status=payload.status,
            changed_by=current_user.email,
        ))

    if payload.assigned_to is not None:
        finding.assigned_to = payload.assigned_to

    if payload.severity and payload.severity != previous_severity:
        if not payload.severity_override_justification:
            raise HTTPException(status_code=400, detail="severity_override_justification is required when changing severity")
        finding.severity = payload.severity
        finding.severity_overridden = True
        finding.severity_override_justification = payload.severity_override_justification
        db.add(AuditLog(
            user_id=current_user.id,
            action="override_severity",
            resource_type="finding",
            resource_id=finding_id,
            details={
                "from": previous_severity,
                "to": payload.severity,
                "justification": payload.severity_override_justification,
            },
        ))

    await db.commit()
    await db.refresh(finding)
    return finding


@router.post("/{finding_id}/notes", response_model=RemediationNoteResponse, status_code=201)
async def add_note(
    finding_id: str,
    payload: RemediationNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Finding not found")
    note = RemediationNote(finding_id=finding_id, author=current_user.email, note=payload.note)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/{finding_id}/notes", response_model=list[RemediationNoteResponse])
async def get_notes(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RemediationNote)
        .where(RemediationNote.finding_id == finding_id)
        .order_by(RemediationNote.created_at.asc())
    )
    return result.scalars().all()


@router.get("/{finding_id}/history", response_model=list[StatusHistoryResponse])
async def get_status_history(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FindingStatusHistory)
        .where(FindingStatusHistory.finding_id == finding_id)
        .order_by(FindingStatusHistory.changed_at.asc())
    )
    return result.scalars().all()
