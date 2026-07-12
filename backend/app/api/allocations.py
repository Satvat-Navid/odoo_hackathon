from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_manager
from ..serializers import allocation_out, transfer_out

router = APIRouter(tags=["allocations"])


def _active_allocation(db: Session, asset_id: int) -> "models.Allocation | None":
    return (
        db.query(models.Allocation)
        .filter(models.Allocation.asset_id == asset_id, models.Allocation.status == "Active")
        .first()
    )


# --- Allocations --------------------------------------------------------------
@router.get("/allocations", response_model=list[schemas.AllocationOut])
def list_allocations(
    db: Session = Depends(get_db), _=Depends(get_current_user), status: Optional[str] = None
):
    query = db.query(models.Allocation)
    if status:
        query = query.filter(models.Allocation.status == status)
    return [allocation_out(a) for a in query.order_by(models.Allocation.id.desc()).all()]


@router.post("/allocations", response_model=schemas.AllocationOut, status_code=201)
def allocate_asset(
    payload: schemas.AllocationCreate,
    db: Session = Depends(get_db),
    current=Depends(require_manager),
):
    asset = db.get(models.Asset, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Conflict rule: an asset already held cannot be re-allocated.
    existing = _active_allocation(db, asset.id)
    if existing:
        holder = existing.employee.full_name if existing.employee else "another user"
        raise HTTPException(
            status_code=409,
            detail=f"Asset {asset.asset_tag} is currently held by {holder}. Raise a transfer request instead.",
        )
    if asset.status in ("Under Maintenance", "Lost", "Retired", "Disposed"):
        raise HTTPException(status_code=400, detail=f"Asset is {asset.status} and cannot be allocated")

    alloc = models.Allocation(
        asset_id=asset.id,
        employee_id=payload.employee_id,
        allocated_by_id=current.id,
        expected_return_date=payload.expected_return_date,
        status="Active",
    )
    asset.status = "Allocated"
    db.add(alloc)
    db.commit()
    db.refresh(alloc)
    return allocation_out(alloc)


@router.post("/allocations/{alloc_id}/return", response_model=schemas.AllocationOut)
def return_asset(
    alloc_id: int,
    payload: schemas.AllocationReturn,
    db: Session = Depends(get_db),
    _=Depends(require_manager),
):
    alloc = db.get(models.Allocation, alloc_id)
    if not alloc or alloc.status != "Active":
        raise HTTPException(status_code=404, detail="Active allocation not found")

    alloc.status = "Returned"
    alloc.returned_date = datetime.now(timezone.utc)
    alloc.checkin_notes = payload.checkin_notes
    if alloc.asset:
        alloc.asset.status = "Available"
        if payload.condition:
            alloc.asset.condition = payload.condition
    db.commit()
    db.refresh(alloc)
    return allocation_out(alloc)


# --- Transfers ----------------------------------------------------------------
@router.get("/transfers", response_model=list[schemas.TransferOut])
def list_transfers(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(models.TransferRequest).order_by(models.TransferRequest.id.desc()).all()
    return [transfer_out(t) for t in rows]


@router.post("/transfers", response_model=schemas.TransferOut, status_code=201)
def request_transfer(
    payload: schemas.TransferCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    asset = db.get(models.Asset, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    active = _active_allocation(db, asset.id)
    transfer = models.TransferRequest(
        asset_id=asset.id,
        from_employee_id=active.employee_id if active else None,
        to_employee_id=payload.to_employee_id,
        requested_by_id=current.id,
        reason=payload.reason,
        status="Requested",
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer_out(transfer)


@router.post("/transfers/{transfer_id}/approve", response_model=schemas.TransferOut)
def approve_transfer(
    transfer_id: int, db: Session = Depends(get_db), current=Depends(require_manager)
):
    transfer = db.get(models.TransferRequest, transfer_id)
    if not transfer or transfer.status != "Requested":
        raise HTTPException(status_code=404, detail="Pending transfer not found")

    # Close the current allocation (if any) and re-allocate to the target holder.
    active = _active_allocation(db, transfer.asset_id)
    if active:
        active.status = "Returned"
        active.returned_date = datetime.now(timezone.utc)
        active.checkin_notes = "Transferred"

    new_alloc = models.Allocation(
        asset_id=transfer.asset_id,
        employee_id=transfer.to_employee_id,
        allocated_by_id=current.id,
        status="Active",
    )
    db.add(new_alloc)
    if transfer.asset:
        transfer.asset.status = "Allocated"
    transfer.status = "Approved"
    db.commit()
    db.refresh(transfer)
    return transfer_out(transfer)


@router.post("/transfers/{transfer_id}/reject", response_model=schemas.TransferOut)
def reject_transfer(
    transfer_id: int, db: Session = Depends(get_db), _=Depends(require_manager)
):
    transfer = db.get(models.TransferRequest, transfer_id)
    if not transfer or transfer.status != "Requested":
        raise HTTPException(status_code=404, detail="Pending transfer not found")
    transfer.status = "Rejected"
    db.commit()
    db.refresh(transfer)
    return transfer_out(transfer)
