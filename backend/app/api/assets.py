from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_manager
from ..serializers import allocation_out, asset_out, maintenance_out

router = APIRouter(prefix="/assets", tags=["assets"])


def _next_asset_tag(db: Session) -> str:
    last = db.query(models.Asset).order_by(models.Asset.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"AF-{next_num:04d}"


@router.get("", response_model=list[schemas.AssetOut])
def list_assets(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    search: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    department_id: Optional[int] = None,
):
    query = db.query(models.Asset)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Asset.name.ilike(like))
            | (models.Asset.asset_tag.ilike(like))
            | (models.Asset.serial_number.ilike(like))
            | (models.Asset.location.ilike(like))
        )
    if status:
        query = query.filter(models.Asset.status == status)
    if category_id:
        query = query.filter(models.Asset.category_id == category_id)
    if department_id:
        query = query.filter(models.Asset.department_id == department_id)
    return [asset_out(a, db) for a in query.order_by(models.Asset.id.desc()).all()]


@router.post("", response_model=schemas.AssetOut, status_code=201)
def register_asset(
    payload: schemas.AssetCreate, db: Session = Depends(get_db), _=Depends(require_manager)
):
    asset = models.Asset(asset_tag=_next_asset_tag(db), **payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset_out(asset, db)


@router.get("/{asset_id}", response_model=schemas.AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset_out(asset, db)


@router.patch("/{asset_id}", response_model=schemas.AssetOut)
def update_asset(
    asset_id: int,
    payload: schemas.AssetUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_manager),
):
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return asset_out(asset, db)


@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: int, db: Session = Depends(get_db), _=Depends(require_manager)):
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    active = (
        db.query(models.Allocation)
        .filter(models.Allocation.asset_id == asset_id, models.Allocation.status == "Active")
        .first()
    )
    if active:
        raise HTTPException(
            status_code=409,
            detail="Asset is currently allocated. Return it before deleting.",
        )
    # Clean up dependent history/bookings/transfers so the row can be removed.
    db.query(models.Allocation).filter(models.Allocation.asset_id == asset_id).delete()
    db.query(models.TransferRequest).filter(models.TransferRequest.asset_id == asset_id).delete()
    db.query(models.Booking).filter(models.Booking.asset_id == asset_id).delete()
    db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.asset_id == asset_id).delete()
    db.delete(asset)
    db.commit()
    return Response(status_code=204)


@router.get("/{asset_id}/history", response_model=list[schemas.AllocationOut])
def asset_history(asset_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    allocations = (
        db.query(models.Allocation)
        .filter(models.Allocation.asset_id == asset_id)
        .order_by(models.Allocation.id.desc())
        .all()
    )
    return [allocation_out(a) for a in allocations]


@router.get("/{asset_id}/maintenance-history", response_model=list[schemas.MaintenanceOut])
def asset_maintenance_history(
    asset_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)
):
    rows = (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.asset_id == asset_id)
        .order_by(models.MaintenanceRequest.id.desc())
        .all()
    )
    return [maintenance_out(m) for m in rows]
