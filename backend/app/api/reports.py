from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.scan import Scan
from app.models.target import AuthorizedTarget
from app.models.finding import Finding
from app.models.report import Report
from app.models.audit import AuditLog
from app.schemas.report import ReportCreate, ReportResponse
from app.api.deps import get_current_user
from app.services.report_service import generate_pdf

router = APIRouter(prefix="/scans", tags=["reports"])


@router.post("/{scan_id}/reports", response_model=ReportResponse, status_code=201)
async def create_report(
    scan_id: str,
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan_result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = scan_result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in ("completed", "completed_with_errors"):
        raise HTTPException(status_code=400, detail="Report can only be generated for completed scans")

    target_result = await db.execute(select(AuthorizedTarget).where(AuthorizedTarget.id == scan.target_id))
    target = target_result.scalar_one_or_none()

    findings_result = await db.execute(
        select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.severity)
    )
    findings = findings_result.scalars().all()

    file_path = generate_pdf(scan, target, findings, current_user.email, payload.executive_summary)

    existing = await db.execute(select(Report).where(Report.scan_id == scan_id))
    existing_reports = existing.scalars().all()
    version = len(existing_reports) + 1

    report = Report(
        scan_id=scan_id,
        generated_by=current_user.email,
        version=version,
        file_path=file_path,
        executive_summary=payload.executive_summary,
    )
    db.add(report)
    db.add(AuditLog(
        user_id=current_user.id,
        action="generate_report",
        resource_type="report",
        resource_id=report.id,
        details={"scan_id": scan_id, "version": version},
    ))
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/{scan_id}/reports", response_model=list[ReportResponse])
async def list_reports(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.scan_id == scan_id).order_by(Report.created_at.desc())
    )
    return result.scalars().all()


router_download = APIRouter(prefix="/reports", tags=["reports"])


@router_download.get("/{report_id}/download")
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not available")
    import os
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file missing from storage")
    filename = f"vapt_report_{report.scan_id[:8]}_v{report.version}.pdf"
    return FileResponse(report.file_path, media_type="application/pdf", filename=filename)
