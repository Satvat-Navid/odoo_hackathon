"""Reports & Analytics — aggregation endpoints returning JSON shaped for charts.

All computation is plain SQL/Python; no heavy dependencies. Manager/Admin only.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..security import require_manager

router = APIRouter(prefix="/reports", tags=["reports"])

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _naive_utc(dt: datetime) -> datetime:
    """Treat stored (SQLite-naive) timestamps as UTC for arithmetic."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _alloc_days(alloc: models.Allocation, now: datetime) -> int:
    start = _naive_utc(alloc.allocated_date) if alloc.allocated_date else now
    end = _naive_utc(alloc.returned_date) if alloc.returned_date else now
    return max((end - start).days, 0)


@router.get("/asset-utilization")
def asset_utilization(db: Session = Depends(get_db), _=Depends(require_manager)):
    now = datetime.now(timezone.utc)
    assets = db.query(models.Asset).all()
    allocations = db.query(models.Allocation).all()

    by_asset: dict[int, dict] = {}
    for a in assets:
        by_asset[a.id] = {
            "asset_id": a.id,
            "asset_tag": a.asset_tag,
            "name": a.name,
            "times_allocated": 0,
            "days_allocated": 0,
        }
    for alloc in allocations:
        row = by_asset.get(alloc.asset_id)
        if not row:
            continue
        row["times_allocated"] += 1
        row["days_allocated"] += _alloc_days(alloc, now)

    rows = sorted(by_asset.values(), key=lambda r: r["days_allocated"], reverse=True)
    idle = [r for r in rows if r["times_allocated"] == 0]
    used = [r for r in rows if r["times_allocated"] > 0]
    return {
        "assets": rows,
        "most_used": used[:5],
        "idle": idle,
        "idle_count": len(idle),
    }


@router.get("/maintenance-frequency")
def maintenance_frequency(db: Session = Depends(get_db), _=Depends(require_manager)):
    requests = db.query(models.MaintenanceRequest).all()
    by_asset: dict[int, dict] = {}
    by_category: dict[str, int] = {}
    for mr in requests:
        asset = mr.asset
        key = mr.asset_id or 0
        if key not in by_asset:
            by_asset[key] = {
                "asset_id": mr.asset_id,
                "asset_tag": asset.asset_tag if asset else "—",
                "name": asset.name if asset else "Unassigned",
                "count": 0,
            }
        by_asset[key]["count"] += 1
        cat = asset.category.name if (asset and asset.category) else "Uncategorised"
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "by_asset": sorted(by_asset.values(), key=lambda r: r["count"], reverse=True),
        "by_category": [
            {"category": k, "count": v}
            for k, v in sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)
        ],
        "total": len(requests),
    }


@router.get("/due-maintenance")
def due_maintenance(db: Session = Depends(get_db), _=Depends(require_manager)):
    today = date.today()
    assets = db.query(models.Asset).all()
    # Pre-count maintenance requests per asset.
    counts: dict[int, int] = {}
    for mr in db.query(models.MaintenanceRequest).all():
        if mr.asset_id:
            counts[mr.asset_id] = counts.get(mr.asset_id, 0) + 1

    flagged = []
    for a in assets:
        reasons = []
        age_months = None
        if a.acquisition_date:
            age_months = (today.year - a.acquisition_date.year) * 12 + (
                today.month - a.acquisition_date.month
            )
        warranty = a.category.warranty_months if a.category else None
        if warranty and age_months is not None and age_months > warranty:
            reasons.append(f"Out of warranty ({age_months}mo > {warranty}mo)")
        if counts.get(a.id, 0) >= 2:
            reasons.append(f"Repeated repairs ({counts[a.id]})")
        if a.condition == "Poor":
            reasons.append("Poor condition")
        if a.status == "Under Maintenance":
            reasons.append("Currently under maintenance")
        if reasons:
            flagged.append({
                "asset_id": a.id,
                "asset_tag": a.asset_tag,
                "name": a.name,
                "category_name": a.category.name if a.category else None,
                "age_months": age_months,
                "condition": a.condition,
                "status": a.status,
                "reasons": reasons,
            })
    return {"items": flagged, "total": len(flagged)}


@router.get("/department-allocation")
def department_allocation(db: Session = Depends(get_db), _=Depends(require_manager)):
    departments = db.query(models.Department).all()
    assets = db.query(models.Asset).all()
    active = (
        db.query(models.Allocation).filter(models.Allocation.status == "Active").all()
    )
    # Map asset -> department for currently-allocated assets.
    asset_dept = {a.id: a.department_id for a in assets}
    total_by_dept: dict[int, int] = {}
    alloc_by_dept: dict[int, int] = {}
    for a in assets:
        if a.department_id:
            total_by_dept[a.department_id] = total_by_dept.get(a.department_id, 0) + 1
    for alloc in active:
        dep_id = alloc.department_id or asset_dept.get(alloc.asset_id)
        if dep_id:
            alloc_by_dept[dep_id] = alloc_by_dept.get(dep_id, 0) + 1

    rows = [
        {
            "department_id": d.id,
            "department": d.name,
            "total_assets": total_by_dept.get(d.id, 0),
            "allocated": alloc_by_dept.get(d.id, 0),
        }
        for d in departments
    ]
    rows.sort(key=lambda r: r["allocated"], reverse=True)
    return {
        "departments": rows,
        "total_allocated": sum(r["allocated"] for r in rows),
        "total_assets": len(assets),
    }


@router.get("/booking-heatmap")
def booking_heatmap(db: Session = Depends(get_db), _=Depends(require_manager)):
    matrix = [[0 for _ in range(24)] for _ in range(7)]
    bookings = (
        db.query(models.Booking).filter(models.Booking.status != "Cancelled").all()
    )
    peak = {"weekday": None, "hour": None, "count": 0}
    for b in bookings:
        start = _naive_utc(b.start_time)
        wd = start.weekday()
        hr = start.hour
        matrix[wd][hr] += 1
        if matrix[wd][hr] > peak["count"]:
            peak = {"weekday": WEEKDAYS[wd], "hour": hr, "count": matrix[wd][hr]}

    return {
        "weekdays": WEEKDAYS,
        "hours": list(range(24)),
        "matrix": matrix,
        "total": len(bookings),
        "peak": peak,
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db), _=Depends(require_manager)):
    today = date.today()
    assets = db.query(models.Asset).all()
    total = len(assets)
    allocated = sum(1 for a in assets if a.status == "Allocated")
    available = sum(1 for a in assets if a.status == "Available")
    under_maintenance = sum(1 for a in assets if a.status == "Under Maintenance")

    allocation_ids = {al.asset_id for al in db.query(models.Allocation).all()}
    idle_assets = sum(1 for a in assets if a.id not in allocation_ids)

    open_maintenance = (
        db.query(models.MaintenanceRequest)
        .filter(
            models.MaintenanceRequest.status.in_(
                ["Pending", "Approved", "Technician Assigned", "In Progress"]
            )
        )
        .count()
    )
    active_allocs = (
        db.query(models.Allocation).filter(models.Allocation.status == "Active").all()
    )
    overdue = sum(
        1 for a in active_allocs if a.expected_return_date and a.expected_return_date < today
    )
    total_bookings = (
        db.query(models.Booking).filter(models.Booking.status != "Cancelled").count()
    )

    return {
        "total_assets": total,
        "allocated": allocated,
        "available": available,
        "under_maintenance": under_maintenance,
        "utilization_rate": round(allocated / total * 100) if total else 0,
        "idle_assets": idle_assets,
        "open_maintenance": open_maintenance,
        "overdue_returns": overdue,
        "total_bookings": total_bookings,
    }
