from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.finding import Finding
from app.models.retest import Retest
from app.models.audit import AuditLog
from app.schemas.report import RetestResponse, RetestComplete
from app.api.deps import get_current_user

router = APIRouter(prefix="/findings", tags=["retests"])


@router.post("/{finding_id}/retests", response_model=RetestResponse, status_code=201)
async def request_retest(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    existing = await db.execute(
        select(Retest).where(Retest.finding_id == finding_id, Retest.status == "pending")
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An open retest already exists for this finding")

    retest = Retest(finding_id=finding_id, requested_by=current_user.email, status="pending")
    db.add(retest)
    db.add(AuditLog(
        user_id=current_user.id,
        action="request_retest",
        resource_type="finding",
        resource_id=finding_id,
    ))
    await db.commit()
    await db.refresh(retest)
    return retest


@router.get("/{finding_id}/retests", response_model=list[RetestResponse])
async def list_retests(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Retest)
        .where(Retest.finding_id == finding_id)
        .order_by(Retest.created_at.desc())
    )
    return result.scalars().all()


retest_router = APIRouter(prefix="/retests", tags=["retests"])


@retest_router.patch("/{retest_id}", response_model=RetestResponse)
async def complete_retest(
    retest_id: str,
    payload: RetestComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Retest).where(Retest.id == retest_id))
    retest = result.scalar_one_or_none()
    if not retest:
        raise HTTPException(status_code=404, detail="Retest not found")
    if retest.status != "pending":
        raise HTTPException(status_code=400, detail="Retest is already completed")

    retest.still_vulnerable = payload.still_vulnerable
    retest.result_summary = payload.result_summary
    retest.confirmed_by = payload.confirmed_by or current_user.email
    retest.status = "completed"
    retest.completed_at = datetime.now(timezone.utc)

    finding_result = await db.execute(select(Finding).where(Finding.id == retest.finding_id))
    finding = finding_result.scalar_one_or_none()
    if finding and not payload.still_vulnerable:
        finding.status = "fixed"

    db.add(AuditLog(
        user_id=current_user.id,
        action="complete_retest",
        resource_type="retest",
        resource_id=retest_id,
        details={"still_vulnerable": payload.still_vulnerable},
    ))
    await db.commit()
    await db.refresh(retest)
    return retest
