from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.user import User
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.target import AuthorizedTarget
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan_counts = await db.execute(
        select(Scan.status, func.count(Scan.id)).group_by(Scan.status)
    )
    scan_by_status = {s: c for s, c in scan_counts.all()}

    finding_counts = await db.execute(
        select(Finding.severity, func.count(Finding.id))
        .where(Finding.status.notin_(["closed", "false_positive"]))
        .group_by(Finding.severity)
    )
    findings_by_severity = {s: c for s, c in finding_counts.all()}

    remediated = await db.execute(
        select(func.count(Finding.id)).where(Finding.status.in_(["fixed", "closed"]))
    )
    remediated_count = remediated.scalar() or 0

    recent_scans_result = await db.execute(
        select(Scan, AuthorizedTarget.name.label("target_name"))
        .join(AuthorizedTarget, Scan.target_id == AuthorizedTarget.id)
        .order_by(Scan.created_at.desc())
        .limit(5)
    )
    recent_scans = [
        {
            "id": scan.id,
            "target": target_name,
            "profile": scan.scan_profile,
            "status": scan.status,
            "created_at": scan.created_at.isoformat(),
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        }
        for scan, target_name in recent_scans_result.all()
    ]

    affected_assets = await db.execute(
        select(AuthorizedTarget.name, func.count(Finding.id).label("finding_count"))
        .join(Finding, Finding.target_id == AuthorizedTarget.id)
        .where(Finding.status.notin_(["closed", "false_positive"]))
        .group_by(AuthorizedTarget.name)
        .order_by(func.count(Finding.id).desc())
        .limit(5)
    )
    most_affected = [{"target": name, "count": count} for name, count in affected_assets.all()]

    total_targets = await db.execute(
        select(func.count(AuthorizedTarget.id)).where(AuthorizedTarget.is_active == True)
    )

    return {
        "scans": {
            "total": sum(scan_by_status.values()),
            "queued": scan_by_status.get("queued", 0),
            "running": scan_by_status.get("running", 0),
            "completed": scan_by_status.get("completed", 0),
            "failed": scan_by_status.get("failed", 0),
            "cancelled": scan_by_status.get("cancelled", 0),
        },
        "findings": {
            "total": sum(findings_by_severity.values()),
            "critical": findings_by_severity.get("critical", 0),
            "high": findings_by_severity.get("high", 0),
            "medium": findings_by_severity.get("medium", 0),
            "low": findings_by_severity.get("low", 0),
            "informational": findings_by_severity.get("informational", 0),
            "remediated": remediated_count,
        },
        "targets": {"total": total_targets.scalar() or 0},
        "recent_scans": recent_scans,
        "most_affected_assets": most_affected,
    }
