from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.target import AuthorizedTarget
from app.models.audit import AuditLog
from app.schemas.target import TargetCreate, TargetUpdate, TargetResponse
from app.api.deps import get_current_user
from app.utils.validators import validate_target_address

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(
    payload: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.authorization_confirmed:
        raise HTTPException(
            status_code=400,
            detail="You must confirm that you are authorized to test this target.",
        )
    if not validate_target_address(payload.address, payload.target_type):
        raise HTTPException(
            status_code=422,
            detail=f"Address '{payload.address}' failed validation for type '{payload.target_type}'.",
        )
    target = AuthorizedTarget(
        **payload.model_dump(exclude={"authorization_confirmed"}),
        authorization_confirmed=True,
        created_by=current_user.id,
    )
    db.add(target)
    await db.flush()
    db.add(AuditLog(
        user_id=current_user.id,
        action="create_target",
        resource_type="target",
        resource_id=target.id,
        details={"name": target.name, "address": target.address},
    ))
    await db.commit()
    await db.refresh(target)
    return target


@router.get("", response_model=list[TargetResponse])
async def list_targets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AuthorizedTarget)
        .where(AuthorizedTarget.is_active == True)
        .order_by(AuthorizedTarget.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AuthorizedTarget).where(AuthorizedTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.patch("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: str,
    payload: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AuthorizedTarget).where(AuthorizedTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(target, field, value)
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_target",
        resource_type="target",
        resource_id=target_id,
    ))
    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/{target_id}", status_code=204)
async def deactivate_target(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AuthorizedTarget).where(AuthorizedTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    target.is_active = False
    db.add(AuditLog(user_id=current_user.id, action="deactivate_target", resource_type="target", resource_id=target_id))
    await db.commit()
