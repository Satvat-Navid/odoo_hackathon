from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..events import log_activity, notify
from ..security import get_current_user
from ..serializers import booking_out

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _overlap(db: Session, resource_name: str, start, end, exclude_id=None):
    query = db.query(models.Booking).filter(
        models.Booking.resource_name == resource_name,
        models.Booking.status != "Cancelled",
        models.Booking.start_time < end,
        models.Booking.end_time > start,
    )
    if exclude_id is not None:
        query = query.filter(models.Booking.id != exclude_id)
    return query.first()


@router.get("", response_model=list[schemas.BookingOut])
def list_bookings(
    db: Session = Depends(get_db), _=Depends(get_current_user), resource: Optional[str] = None
):
    query = db.query(models.Booking)
    if resource:
        query = query.filter(models.Booking.resource_name == resource)
    return [booking_out(b) for b in query.order_by(models.Booking.start_time).all()]


@router.post("", response_model=schemas.BookingOut, status_code=201)
def create_booking(
    payload: schemas.BookingCreate, db: Session = Depends(get_db), current=Depends(get_current_user)
):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Overlap validation: reject if the requested slot overlaps an existing,
    # non-cancelled booking for the same resource. Adjacent slots are fine
    # (start == other end), so we use strict inequality on both edges.
    overlap = _overlap(db, payload.resource_name, payload.start_time, payload.end_time)
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{payload.resource_name} is already booked from "
                f"{overlap.start_time:%H:%M} to {overlap.end_time:%H:%M}."
            ),
        )

    booking = models.Booking(
        asset_id=payload.asset_id,
        resource_name=payload.resource_name,
        booked_by_id=current.id,
        booked_by=current.full_name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        purpose=payload.purpose,
        status="Upcoming",
    )
    db.add(booking)
    log_activity(
        db, current, "booking.created", "booking", None,
        f"{current.full_name} booked {payload.resource_name}",
    )
    notify(db, current.id, "booking",
           f"Booking confirmed for {payload.resource_name}.", "/bookings")
    db.commit()
    db.refresh(booking)
    return booking_out(booking)


@router.post("/{booking_id}/reschedule", response_model=schemas.BookingOut)
def reschedule_booking(
    booking_id: int,
    payload: schemas.BookingReschedule,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Cancelled bookings cannot be rescheduled.")
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    overlap = _overlap(db, booking.resource_name, payload.start_time, payload.end_time, booking.id)
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{booking.resource_name} is already booked from "
                f"{overlap.start_time:%H:%M} to {overlap.end_time:%H:%M}."
            ),
        )
    booking.start_time = payload.start_time
    booking.end_time = payload.end_time
    booking.status = "Upcoming"
    log_activity(
        db, current, "booking.rescheduled", "booking", booking.id,
        f"{current.full_name} rescheduled {booking.resource_name}",
    )
    notify(db, booking.booked_by_id, "booking",
           f"Your {booking.resource_name} booking was rescheduled.", "/bookings")
    db.commit()
    db.refresh(booking)
    return booking_out(booking)


@router.post("/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(
    booking_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)
):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "Cancelled"
    log_activity(
        db, current, "booking.cancelled", "booking", booking.id,
        f"{current.full_name} cancelled {booking.resource_name}",
    )
    notify(db, booking.booked_by_id, "booking",
           f"Your {booking.resource_name} booking was cancelled.", "/bookings")
    db.commit()
    db.refresh(booking)
    return booking_out(booking)
