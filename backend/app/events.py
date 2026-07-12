"""Lightweight, dependency-light helpers for Activity Logs & Notifications.

Any router can call ``log_activity`` / ``notify`` inside its own transaction —
these only ``db.add`` rows; the caller is responsible for the surrounding
``db.commit()``. The on-fetch alert checks (overdue returns, booking reminders)
own their transaction and commit themselves.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from . import models
from .security import ROLE_ADMIN


def log_activity(
    db: Session,
    actor: Optional[models.Employee],
    action: str,
    entity_type: Optional[str],
    entity_id: Optional[int],
    summary: str,
) -> None:
    """Append an immutable activity-log row (does not commit)."""
    db.add(
        models.ActivityLog(
            actor_id=actor.id if actor else None,
            actor_name=actor.full_name if actor else "System",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
        )
    )


def notify(
    db: Session,
    user_id: Optional[int],
    type: str,
    message: str,
    link: Optional[str] = None,
    dedupe_key: Optional[str] = None,
) -> None:
    """Queue a notification for one recipient (does not commit).

    When ``dedupe_key`` is given, a matching notification for the same user is
    only created once — used by the recurring alert checks.
    """
    if not user_id:
        return
    if dedupe_key:
        exists = (
            db.query(models.Notification)
            .filter(
                models.Notification.user_id == user_id,
                models.Notification.dedupe_key == dedupe_key,
            )
            .first()
        )
        if exists:
            return
    db.add(
        models.Notification(
            user_id=user_id,
            type=type,
            message=message,
            link=link,
            dedupe_key=dedupe_key,
            is_read=False,
        )
    )


def notify_admins(
    db: Session,
    type: str,
    message: str,
    link: Optional[str] = None,
    dedupe_key: Optional[str] = None,
) -> None:
    """Notify every active Admin (used for org-wide alerts like discrepancies)."""
    admins = (
        db.query(models.Employee)
        .filter(models.Employee.role == ROLE_ADMIN, models.Employee.status == "Active")
        .all()
    )
    for a in admins:
        notify(db, a.id, type, message, link, dedupe_key)


# --- On-fetch alert checks ----------------------------------------------------
def run_alert_checks(db: Session) -> None:
    """Cheap idempotent sweep invoked when notifications are fetched.

    Creates one-off alerts for overdue allocations and imminent bookings.
    Deduped via ``dedupe_key`` so repeated fetches don't pile up duplicates.
    No background scheduler required.
    """
    _check_overdue_returns(db)
    _check_booking_reminders(db)
    db.commit()


def _check_overdue_returns(db: Session) -> None:
    today = date.today()
    overdue = (
        db.query(models.Allocation)
        .filter(models.Allocation.status == "Active")
        .all()
    )
    for alloc in overdue:
        if not alloc.expected_return_date or alloc.expected_return_date >= today:
            continue
        tag = alloc.asset.asset_tag if alloc.asset else f"#{alloc.asset_id}"
        name = alloc.asset.name if alloc.asset else ""
        msg = f"Overdue Return Alert: {tag} {name} was due {alloc.expected_return_date:%b %d}."
        key = f"overdue:{alloc.id}"
        # Tell the holder and whoever allocated it.
        notify(db, alloc.employee_id, "overdue", msg, "/allocations", key)
        notify(db, alloc.allocated_by_id, "overdue", msg, "/allocations", key)


def _check_booking_reminders(db: Session) -> None:
    now = datetime.now(timezone.utc)
    soon = now + timedelta(hours=1)
    upcoming = (
        db.query(models.Booking)
        .filter(models.Booking.status == "Upcoming")
        .all()
    )
    for bk in upcoming:
        start = bk.start_time
        # Normalise naive timestamps (SQLite drops tzinfo) to UTC for comparison.
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if now <= start <= soon:
            msg = f"Reminder: {bk.resource_name} booking starts at {start:%H:%M}."
            notify(db, bk.booked_by_id, "booking", msg, "/bookings", f"booking-reminder:{bk.id}")
