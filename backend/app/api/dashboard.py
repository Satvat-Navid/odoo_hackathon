from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..security import get_current_user
from ..serializers import allocation_out, booking_out

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis")
def kpis(db: Session = Depends(get_db), _=Depends(get_current_user)):
    today = date.today()
    now = datetime.now(timezone.utc)
    week_ahead = today + timedelta(days=7)

    assets = db.query(models.Asset).all()
    status_counts: dict[str, int] = {}
    for a in assets:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1

    active_allocs = (
        db.query(models.Allocation).filter(models.Allocation.status == "Active").all()
    )
    overdue = [a for a in active_allocs if a.expected_return_date and a.expected_return_date < today]
    upcoming = [
        a
        for a in active_allocs
        if a.expected_return_date and today <= a.expected_return_date <= week_ahead
    ]

    active_bookings = (
        db.query(models.Booking).filter(models.Booking.status.in_(["Upcoming", "Ongoing"])).count()
    )
    pending_transfers = (
        db.query(models.TransferRequest)
        .filter(models.TransferRequest.status == "Requested")
        .count()
    )
    maintenance_today = (
        db.query(models.MaintenanceRequest)
        .filter(models.MaintenanceRequest.status.in_(["Pending", "Approved", "In Progress"]))
        .count()
    )

    return {
        "assets_available": status_counts.get("Available", 0),
        "assets_allocated": status_counts.get("Allocated", 0),
        "under_maintenance": status_counts.get("Under Maintenance", 0),
        "maintenance_today": maintenance_today,
        "active_bookings": active_bookings,
        "pending_transfers": pending_transfers,
        "upcoming_returns": len(upcoming),
        "overdue_returns": len(overdue),
        "total_assets": len(assets),
        "status_breakdown": status_counts,
        "overdue_list": [allocation_out(a) for a in overdue],
        "upcoming_list": [allocation_out(a) for a in upcoming],
    }
