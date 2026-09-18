import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.user import User
from app.models.scan import Scan, ScanJob
from app.models.target import AuthorizedTarget
from app.models.finding import Finding
from app.models.audit import AuditLog
from app.schemas.scan import ScanCreate, ScanResponse, ScanSummary
from app.api.deps import get_current_user
from app.core.security import decode_token
from app.workers.scan_tasks import orchestrate_scan

router = APIRouter(prefix="/scans", tags=["scans"])

TOOL_VALIDATORS = {
    "nmap": ["host_ip", "web_application", "api"],
    "zap": ["web_application", "api"],
    "trivy": ["docker_image"],
    "semgrep": ["source_repository"],
}


@router.post("", response_model=dict, status_code=202)
async def create_scan(
    payload: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AuthorizedTarget).where(
            AuthorizedTarget.id == payload.target_id,
            AuthorizedTarget.is_active == True,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Authorized target not found")
    if not target.authorization_confirmed:
        raise HTTPException(status_code=403, detail="Target has not been confirmed as authorized for scanning")

    for tool in payload.tools:
        allowed_types = TOOL_VALIDATORS.get(tool, [])
        if allowed_types and target.target_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool}' is not compatible with target type '{target.target_type}'",
            )

    scan = Scan(
        target_id=payload.target_id,
        created_by=current_user.id,
        scan_profile=payload.scan_profile,
        tools=payload.tools,
        intensity=payload.intensity,
        scan_options=payload.scan_options,
        status="queued",
    )
    db.add(scan)
    await db.flush()

    for tool in payload.tools:
        db.add(ScanJob(scan_id=scan.id, tool=tool, status="queued"))

    db.add(AuditLog(
        user_id=current_user.id,
        action="create_scan",
        resource_type="scan",
        resource_id=scan.id,
        details={"target": target.name, "tools": payload.tools},
    ))
    await db.commit()
    await db.refresh(scan)

    orchestrate_scan.apply_async(args=[scan.id], queue="scans")

    return {"scan_id": scan.id, "status": "queued"}


@router.get("", response_model=list[ScanResponse])
async def list_scans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.jobs)).order_by(Scan.created_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.get("/compare", response_model=dict)
async def compare_scans(
    scan_a: str,
    scan_b: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare two scans by fingerprint: new, resolved, and persisting findings."""
    for sid in (scan_a, scan_b):
        r = await db.execute(select(Scan).where(Scan.id == sid))
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Scan {sid} not found")

    res_a = await db.execute(select(Finding).where(Finding.scan_id == scan_a))
    res_b = await db.execute(select(Finding).where(Finding.scan_id == scan_b))
    findings_a = res_a.scalars().all()
    findings_b = res_b.scalars().all()

    fp_a = {f.fingerprint: f for f in findings_a if f.fingerprint}
    fp_b = {f.fingerprint: f for f in findings_b if f.fingerprint}

    def _finding_dict(f):
        return {
            "id": f.id, "title": f.title, "severity": f.severity,
            "source_tool": f.source_tool, "affected_resource": f.affected_resource,
            "status": f.status, "cve": f.cve, "fingerprint": f.fingerprint,
        }

    new_findings = [_finding_dict(fp_b[fp]) for fp in fp_b if fp not in fp_a]
    resolved_findings = [_finding_dict(fp_a[fp]) for fp in fp_a if fp not in fp_b]
    persisting_findings = [_finding_dict(fp_b[fp]) for fp in fp_b if fp in fp_a]

    return {
        "scan_a_id": scan_a,
        "scan_b_id": scan_b,
        "new_findings": new_findings,
        "resolved_findings": resolved_findings,
        "persisting_findings": persisting_findings,
        "summary": {
            "new": len(new_findings),
            "resolved": len(resolved_findings),
            "persisting": len(persisting_findings),
        },
    }


@router.get("/history/summary", response_model=list[ScanSummary])
async def scan_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan, AuthorizedTarget.name.label("target_name"))
        .join(AuthorizedTarget, Scan.target_id == AuthorizedTarget.id)
        .order_by(Scan.created_at.desc())
        .limit(50)
    )
    rows = result.all()
    summaries = []
    for scan, target_name in rows:
        findings_result = await db.execute(
            select(Finding.severity, func.count(Finding.id))
            .where(Finding.scan_id == scan.id)
            .group_by(Finding.severity)
        )
        counts = {sev: cnt for sev, cnt in findings_result.all()}
        summaries.append(ScanSummary(
            id=scan.id,
            target_id=scan.target_id,
            target_name=target_name,
            scan_profile=scan.scan_profile,
            status=scan.status,
            created_at=scan.created_at,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            critical_count=counts.get("critical", 0),
            high_count=counts.get("high", 0),
            medium_count=counts.get("medium", 0),
            low_count=counts.get("low", 0),
            info_count=counts.get("informational", 0),
        ))
    return summaries


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.jobs)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/{scan_id}/cancel", response_model=dict)
async def cancel_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in ("queued", "running"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel scan in status: {scan.status}")
    scan.status = "cancelled"
    scan.completed_at = datetime.now(timezone.utc)
    db.add(AuditLog(user_id=current_user.id, action="cancel_scan", resource_type="scan", resource_id=scan_id))
    await db.commit()
    return {"scan_id": scan_id, "status": "cancelled"}


async def _get_user_from_token_param(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Auth dependency for SSE — reads token from query param (EventSource can't set headers)."""
    user_id = decode_token(token)
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


@router.get("/{scan_id}/stream")
async def stream_scan_progress(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user_from_token_param),
):
    """Server-Sent Events endpoint for real-time scan progress."""
    async def event_generator():
        for _ in range(300):  # max 5 min polling
            result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = result.scalar_one_or_none()
            if not scan:
                break
            data = json.dumps({
                "scan_id": scan_id,
                "status": scan.status,
                "progress": scan.progress,
            })
            yield f"data: {data}\n\n"
            if scan.status in ("completed", "failed", "cancelled", "completed_with_errors"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
