from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..events import log_activity, notify
from ..security import ROLE_DEPARTMENT_HEAD, get_current_user, require_manager
from ..serializers import allocation_out, transfer_out

router = APIRouter(tags=["allocations"])


def _active_allocation(db: Session, asset_id: int) -> "models.Allocation | None":
    return (
        db.query(models.Allocation)
        .filter(models.Allocation.asset_id == asset_id, models.Allocation.status == "Active")
        .first()
    )


def _in_scope(user: models.Employee, asset: "models.Asset | None") -> bool:
    """Department Heads are scoped to their own department; other managers are
    org-wide (Admin is always org-wide via require_manager)."""
    if user.role != ROLE_DEPARTMENT_HEAD:
        return True
    return bool(asset) and asset.department_id == user.department_id


def _scope_allocations(query, user: models.Employee):
    """Restrict a query of allocations to a Department Head's department."""
    if user.role == ROLE_DEPARTMENT_HEAD:
        query = query.join(models.Asset, models.Allocation.asset_id == models.Asset.id).filter(
            models.Asset.department_id == user.department_id
        )
    return query


def _dept_head(db: Session, department_id: int) -> Optional[int]:
    dep = db.get(models.Department, department_id)
    return dep.head_id if dep else None


# --- Allocations --------------------------------------------------------------
@router.get("/allocations", response_model=list[schemas.AllocationOut])
def list_allocations(
    db: Session = Depends(get_db), current=Depends(get_current_user), status: Optional[str] = None
):
    query = db.query(models.Allocation)
    if status:
        query = query.filter(models.Allocation.status == status)
    query = _scope_allocations(query, current)
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

    # Exactly one target: an employee OR a department.
    if bool(payload.employee_id) == bool(payload.department_id):
        raise HTTPException(
            status_code=400, detail="Allocate to either an employee or a department."
        )
    if not _in_scope(current, asset):
        raise HTTPException(
            status_code=403, detail="You can only allocate assets in your department."
        )

    # Conflict rule: an asset already held cannot be re-allocated.
    existing = _active_allocation(db, asset.id)
    if existing:
        holder = existing.employee.full_name if existing.employee else (
            existing.department.name if existing.department else "another holder"
        )
        raise HTTPException(
            status_code=409,
            detail=f"Asset {asset.asset_tag} is currently held by {holder}. Raise a transfer request instead.",
        )
    if asset.status in ("Under Maintenance", "Lost", "Retired", "Disposed"):
        raise HTTPException(status_code=400, detail=f"Asset is {asset.status} and cannot be allocated")

    target_name = None
    notify_user_id = None
    if payload.employee_id:
        emp = db.get(models.Employee, payload.employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        target_name = emp.full_name
        notify_user_id = emp.id
    else:
        dep = db.get(models.Department, payload.department_id)
        if not dep:
            raise HTTPException(status_code=404, detail="Department not found")
        target_name = f"Dept: {dep.name}"
        notify_user_id = dep.head_id  # tell the department head

    alloc = models.Allocation(
        asset_id=asset.id,
        employee_id=payload.employee_id,
        department_id=payload.department_id,
        allocated_by_id=current.id,
        expected_return_date=payload.expected_return_date,
        status="Active",
    )
    asset.status = "Allocated"
    db.add(alloc)

    summary = f"{current.full_name} allocated {asset.asset_tag} ({asset.name}) to {target_name}"
    log_activity(db, current, "asset.allocated", "asset", asset.id, summary)
    notify(
        db, notify_user_id, "allocation",
        f"{asset.asset_tag} {asset.name} was allocated to you.", "/allocations",
    )
    db.commit()
    db.refresh(alloc)
    return allocation_out(alloc)


@router.post("/allocations/{alloc_id}/return", response_model=schemas.AllocationOut)
def return_asset(
    alloc_id: int,
    payload: schemas.AllocationReturn,
    db: Session = Depends(get_db),
    current=Depends(require_manager),
):
    alloc = db.get(models.Allocation, alloc_id)
    if not alloc or alloc.status != "Active":
        raise HTTPException(status_code=404, detail="Active allocation not found")
    if not _in_scope(current, alloc.asset):
        raise HTTPException(status_code=403, detail="Out of your department scope.")

    alloc.status = "Returned"
    alloc.returned_date = datetime.now(timezone.utc)
    alloc.checkin_notes = payload.checkin_notes
    if alloc.asset:
        alloc.asset.status = "Available"
        if payload.condition:
            alloc.asset.condition = payload.condition
        tag = alloc.asset.asset_tag
    else:
        tag = f"#{alloc.asset_id}"
    log_activity(
        db, current, "asset.returned", "asset", alloc.asset_id,
        f"{current.full_name} checked in {tag}",
    )
    db.commit()
    db.refresh(alloc)
    return allocation_out(alloc)


# --- Transfers ----------------------------------------------------------------
@router.get("/transfers", response_model=list[schemas.TransferOut])
def list_transfers(db: Session = Depends(get_db), current=Depends(get_current_user)):
    query = db.query(models.TransferRequest)
    if current.role == ROLE_DEPARTMENT_HEAD:
        query = query.join(models.Asset, models.TransferRequest.asset_id == models.Asset.id).filter(
            models.Asset.department_id == current.department_id
        )
    rows = query.order_by(models.TransferRequest.id.desc()).all()
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
    log_activity(
        db, current, "transfer.requested", "asset", asset.id,
        f"{current.full_name} requested a transfer of {asset.asset_tag}",
    )
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
    if not _in_scope(current, transfer.asset):
        raise HTTPException(status_code=403, detail="Out of your department scope.")

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

    tag = transfer.asset.asset_tag if transfer.asset else f"#{transfer.asset_id}"
    log_activity(
        db, current, "transfer.approved", "asset", transfer.asset_id,
        f"{current.full_name} approved transfer of {tag}",
    )
    notify(db, transfer.to_employee_id, "transfer", f"{tag} was transferred to you.", "/allocations")
    if transfer.requested_by_id and transfer.requested_by_id != transfer.to_employee_id:
        notify(db, transfer.requested_by_id, "transfer",
               f"Your transfer request for {tag} was approved.", "/allocations")
    db.commit()
    db.refresh(transfer)
    return transfer_out(transfer)


@router.post("/transfers/{transfer_id}/reject", response_model=schemas.TransferOut)
def reject_transfer(
    transfer_id: int, db: Session = Depends(get_db), current=Depends(require_manager)
):
    transfer = db.get(models.TransferRequest, transfer_id)
    if not transfer or transfer.status != "Requested":
        raise HTTPException(status_code=404, detail="Pending transfer not found")
    if not _in_scope(current, transfer.asset):
        raise HTTPException(status_code=403, detail="Out of your department scope.")
    transfer.status = "Rejected"
    tag = transfer.asset.asset_tag if transfer.asset else f"#{transfer.asset_id}"
    log_activity(
        db, current, "transfer.rejected", "asset", transfer.asset_id,
        f"{current.full_name} rejected transfer of {tag}",
    )
    notify(db, transfer.requested_by_id, "transfer",
           f"Your transfer request for {tag} was rejected.", "/allocations")
    db.commit()
    db.refresh(transfer)
    return transfer_out(transfer)
