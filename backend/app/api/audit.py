from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..events import log_activity, notify_admins
from ..security import ROLE_ADMIN, get_current_user, require_admin
from ..serializers import audit_cycle_detail, audit_cycle_out, audit_item_out

router = APIRouter(tags=["audit"])


def _scoped_assets(db: Session, scope_type: str, scope_value):
    """Return the assets covered by a cycle's scope."""
    query = db.query(models.Asset)
    if scope_type == "Department":
        query = query.join(models.Department, models.Asset.department_id == models.Department.id).filter(
            models.Department.name == scope_value
        )
    elif scope_type == "Location":
        query = query.filter(models.Asset.location == scope_value)
    # "All" -> no additional filter
    return query.all()


def _get_cycle(db: Session, cycle_id: int) -> models.AuditCycle:
    cycle = db.get(models.AuditCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Audit cycle not found")
    return cycle


def _is_assigned(db: Session, cycle_id: int, user: models.Employee) -> bool:
    return (
        db.query(models.AuditAssignment)
        .filter(
            models.AuditAssignment.cycle_id == cycle_id,
            models.AuditAssignment.auditor_id == user.id,
        )
        .first()
        is not None
    )


# --- Cycles -------------------------------------------------------------------
@router.get("/audit-cycles", response_model=list[schemas.AuditCycleOut])
def list_cycles(db: Session = Depends(get_db), _=Depends(get_current_user)):
    cycles = db.query(models.AuditCycle).order_by(models.AuditCycle.id.desc()).all()
    return [audit_cycle_out(c) for c in cycles]


@router.post("/audit-cycles", response_model=schemas.AuditCycleOut, status_code=201)
def create_cycle(
    payload: schemas.AuditCycleCreate,
    db: Session = Depends(get_db),
    current=Depends(require_admin),
):
    if payload.scope_type not in ("Department", "Location", "All"):
        raise HTTPException(status_code=400, detail="Invalid scope type")
    if payload.scope_type != "All" and not payload.scope_value:
        raise HTTPException(status_code=400, detail="scope_value is required for this scope")

    cycle = models.AuditCycle(
        name=payload.name,
        scope_type=payload.scope_type,
        scope_value=payload.scope_value if payload.scope_type != "All" else None,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="Open",
        created_by_id=current.id,
    )
    db.add(cycle)
    db.flush()

    # Auto-generate a Pending audit item for every asset matching the scope.
    for asset in _scoped_assets(db, cycle.scope_type, cycle.scope_value):
        db.add(models.AuditItem(cycle_id=cycle.id, asset_id=asset.id, result="Pending"))

    db.commit()
    db.refresh(cycle)
    return audit_cycle_out(cycle)


@router.get("/audit-cycles/{cycle_id}")
def get_cycle(cycle_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cycle = _get_cycle(db, cycle_id)
    return audit_cycle_detail(cycle)


@router.post("/audit-cycles/{cycle_id}/auditors")
def assign_auditors(
    cycle_id: int,
    payload: schemas.AuditorsAssign,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    cycle = _get_cycle(db, cycle_id)
    if cycle.status == "Closed":
        raise HTTPException(status_code=400, detail="Cycle is closed and cannot be edited.")

    existing = {a.auditor_id for a in cycle.assignments}
    for auditor_id in payload.auditor_ids:
        if auditor_id in existing:
            continue
        if not db.get(models.Employee, auditor_id):
            raise HTTPException(status_code=404, detail=f"Employee #{auditor_id} not found")
        db.add(models.AuditAssignment(cycle_id=cycle.id, auditor_id=auditor_id))
    db.commit()
    db.refresh(cycle)
    return audit_cycle_detail(cycle)


@router.patch("/audit-items/{item_id}", response_model=schemas.AuditItemOut)
def update_item(
    item_id: int,
    payload: schemas.AuditItemUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    item = db.get(models.AuditItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Audit item not found")
    cycle = item.cycle
    if cycle.status == "Closed":
        raise HTTPException(status_code=400, detail="Cycle is closed; items are locked.")
    # Only the admin or an assigned auditor may record a result.
    if current.role != ROLE_ADMIN and not _is_assigned(db, cycle.id, current):
        raise HTTPException(
            status_code=403, detail="You are not assigned to audit this cycle."
        )
    if payload.result not in ("Pending", "Verified", "Missing", "Damaged"):
        raise HTTPException(status_code=400, detail="Invalid result")

    item.result = payload.result
    item.notes = payload.notes
    item.checked_by_id = current.id
    item.checked_at = datetime.now(timezone.utc)

    # A Missing/Damaged result is a discrepancy — alert the admins.
    if payload.result in ("Missing", "Damaged"):
        tag = item.asset.asset_tag if item.asset else f"#{item.asset_id}"
        summary = f"{current.full_name} flagged {tag} as {payload.result} in '{cycle.name}'"
        log_activity(db, current, "audit.discrepancy", "asset", item.asset_id, summary)
        notify_admins(
            db, "audit", f"Audit discrepancy: {tag} flagged {payload.result} in '{cycle.name}'.",
            "/audit", f"discrepancy:{item.id}:{payload.result}",
        )
    db.commit()
    db.refresh(item)
    return audit_item_out(item)


@router.get("/audit-cycles/{cycle_id}/discrepancies")
def discrepancies(cycle_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cycle = _get_cycle(db, cycle_id)
    flagged = [i for i in cycle.items if i.result in ("Missing", "Damaged")]
    return {
        "cycle_id": cycle.id,
        "cycle_name": cycle.name,
        "missing_count": sum(1 for i in flagged if i.result == "Missing"),
        "damaged_count": sum(1 for i in flagged if i.result == "Damaged"),
        "total": len(flagged),
        "items": [audit_item_out(i) for i in sorted(flagged, key=lambda x: x.id)],
    }


@router.post("/audit-cycles/{cycle_id}/close")
def close_cycle(cycle_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    cycle = _get_cycle(db, cycle_id)
    if cycle.status == "Closed":
        raise HTTPException(status_code=400, detail="Cycle is already closed.")

    # Apply confirmed discrepancies to the affected assets.
    for item in cycle.items:
        if not item.asset:
            continue
        if item.result == "Missing":
            item.asset.status = "Lost"
        elif item.result == "Damaged":
            item.asset.condition = "Poor"
        # Verified / Pending items are left untouched.

    cycle.status = "Closed"
    cycle.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cycle)
    return audit_cycle_detail(cycle)
