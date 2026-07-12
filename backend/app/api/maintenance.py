from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_manager
from ..serializers import maintenance_out

router = APIRouter(prefix="/maintenance-requests", tags=["maintenance"])

# Asset lifecycle states that block a maintenance approval.
_BLOCKED_STATES = ("Lost", "Retired", "Disposed")


def _get_request(db: Session, request_id: int) -> models.MaintenanceRequest:
    mr = db.get(models.MaintenanceRequest, request_id)
    if not mr:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return mr


def _require_status(mr: models.MaintenanceRequest, expected: str) -> None:
    """Enforce the workflow state machine — reject invalid transitions with 400."""
    if mr.status != expected:
        raise HTTPException(
            status_code=400,
            detail=f"Request is '{mr.status}'; this action requires '{expected}'.",
        )


@router.get("", response_model=list[schemas.MaintenanceOut])
def list_requests(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    status: Optional[str] = None,
):
    query = db.query(models.MaintenanceRequest)
    if status:
        query = query.filter(models.MaintenanceRequest.status == status)
    rows = query.order_by(models.MaintenanceRequest.id.desc()).all()
    return [maintenance_out(m) for m in rows]


@router.post("", response_model=schemas.MaintenanceOut, status_code=201)
def raise_request(
    payload: schemas.MaintenanceCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """Any authenticated user (incl. Employee) can raise a maintenance request."""
    asset = db.get(models.Asset, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    mr = models.MaintenanceRequest(
        asset_id=asset.id,
        requester_name=current.full_name,
        description=payload.description,
        priority=payload.priority,
        photo_url=payload.photo_url,
        status="Pending",
    )
    db.add(mr)
    db.commit()
    db.refresh(mr)
    return maintenance_out(mr)


@router.post("/{request_id}/approve", response_model=schemas.MaintenanceOut)
def approve_request(
    request_id: int, db: Session = Depends(get_db), current=Depends(require_manager)
):
    mr = _get_request(db, request_id)
    _require_status(mr, "Pending")
    if mr.asset and mr.asset.status in _BLOCKED_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Asset is {mr.asset.status} and cannot go under maintenance.",
        )
    mr.status = "Approved"
    mr.approved_by_id = current.id
    if mr.asset:
        mr.asset.status = "Under Maintenance"
    db.commit()
    db.refresh(mr)
    return maintenance_out(mr)


@router.post("/{request_id}/reject", response_model=schemas.MaintenanceOut)
def reject_request(
    request_id: int, db: Session = Depends(get_db), current=Depends(require_manager)
):
    mr = _get_request(db, request_id)
    _require_status(mr, "Pending")
    mr.status = "Rejected"
    mr.approved_by_id = current.id
    db.commit()
    db.refresh(mr)
    return maintenance_out(mr)


@router.post("/{request_id}/assign", response_model=schemas.MaintenanceOut)
def assign_technician(
    request_id: int,
    payload: schemas.MaintenanceAssign,
    db: Session = Depends(get_db),
    _=Depends(require_manager),
):
    mr = _get_request(db, request_id)
    _require_status(mr, "Approved")
    mr.technician_name = payload.technician
    mr.status = "Technician Assigned"
    db.commit()
    db.refresh(mr)
    return maintenance_out(mr)


@router.post("/{request_id}/start", response_model=schemas.MaintenanceOut)
def start_request(
    request_id: int, db: Session = Depends(get_db), _=Depends(require_manager)
):
    mr = _get_request(db, request_id)
    _require_status(mr, "Technician Assigned")
    mr.status = "In Progress"
    db.commit()
    db.refresh(mr)
    return maintenance_out(mr)


@router.post("/{request_id}/resolve", response_model=schemas.MaintenanceOut)
def resolve_request(
    request_id: int,
    payload: schemas.MaintenanceResolve,
    db: Session = Depends(get_db),
    _=Depends(require_manager),
):
    mr = _get_request(db, request_id)
    _require_status(mr, "In Progress")
    mr.status = "Resolved"
    mr.resolution_notes = payload.resolution_notes
    if mr.asset:
        mr.asset.status = "Available"
    db.commit()
    db.refresh(mr)
    return maintenance_out(mr)
