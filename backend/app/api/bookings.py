from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..serializers import booking_out

router = APIRouter(prefix="/bookings", tags=["bookings"])


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
    overlap = (
        db.query(models.Booking)
        .filter(
            models.Booking.resource_name == payload.resource_name,
            models.Booking.status != "Cancelled",
            models.Booking.start_time < payload.end_time,
            models.Booking.end_time > payload.start_time,
        )
        .first()
    )
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
    db.commit()
    db.refresh(booking)
    return booking_out(booking)
