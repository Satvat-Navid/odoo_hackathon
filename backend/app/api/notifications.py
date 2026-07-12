from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..events import run_alert_checks
from ..security import get_current_user, require_manager
from ..serializers import activity_log_out, notification_out

router = APIRouter(tags=["notifications"])


# --- Notifications (per-user) -------------------------------------------------
@router.get("/notifications", response_model=list[schemas.NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
    unread_only: bool = False,
):
    run_alert_checks(db)  # lazily materialise overdue / reminder alerts
    query = db.query(models.Notification).filter(models.Notification.user_id == current.id)
    if unread_only:
        query = query.filter(models.Notification.is_read == False)  # noqa: E712
    rows = query.order_by(models.Notification.id.desc()).limit(50).all()
    return [notification_out(n) for n in rows]


@router.get("/notifications/unread-count", response_model=schemas.UnreadCountOut)
def unread_count(db: Session = Depends(get_db), current=Depends(get_current_user)):
    run_alert_checks(db)
    count = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current.id, models.Notification.is_read == False)  # noqa: E712
        .count()
    )
    return {"unread": count}


@router.post("/notifications/{notif_id}/read", response_model=schemas.NotificationOut)
def mark_read(notif_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    notif = db.get(models.Notification, notif_id)
    if not notif or notif.user_id != current.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notification_out(notif)


@router.post("/notifications/read-all", response_model=schemas.UnreadCountOut)
def mark_all_read(db: Session = Depends(get_db), current=Depends(get_current_user)):
    db.query(models.Notification).filter(
        models.Notification.user_id == current.id,
        models.Notification.is_read == False,  # noqa: E712
    ).update({models.Notification.is_read: True})
    db.commit()
    return {"unread": 0}


# --- Activity log (managers/admin only) ---------------------------------------
@router.get("/activity-logs", response_model=list[schemas.ActivityLogOut])
def list_activity(
    db: Session = Depends(get_db),
    _=Depends(require_manager),
    entity_type: Optional[str] = None,
    actor_id: Optional[int] = None,
    limit: int = 100,
):
    query = db.query(models.ActivityLog)
    if entity_type:
        query = query.filter(models.ActivityLog.entity_type == entity_type)
    if actor_id:
        query = query.filter(models.ActivityLog.actor_id == actor_id)
    rows = query.order_by(models.ActivityLog.id.desc()).limit(min(limit, 500)).all()
    return [activity_log_out(r) for r in rows]
