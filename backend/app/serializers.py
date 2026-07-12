"""Model -> response-dict helpers that flatten related names for the UI."""
from datetime import date, datetime, timezone

from . import models


def employee_out(emp: models.Employee) -> dict:
    return {
        "id": emp.id,
        "full_name": emp.full_name,
        "email": emp.email,
        "department_id": emp.department_id,
        "department_name": emp.department.name if emp.department else None,
        "role": emp.role,
        "status": emp.status,
    }


def department_out(dep: models.Department) -> dict:
    return {
        "id": dep.id,
        "name": dep.name,
        "head_id": dep.head_id,
        "head_name": dep.head.full_name if dep.head else None,
        "parent_id": dep.parent_id,
        "status": dep.status,
    }


def category_out(cat: models.AssetCategory) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "description": cat.description,
        "warranty_months": cat.warranty_months,
    }


def _active_holder(asset: models.Asset, db) -> "str | None":
    alloc = (
        db.query(models.Allocation)
        .filter(models.Allocation.asset_id == asset.id, models.Allocation.status == "Active")
        .first()
    )
    return alloc.employee.full_name if alloc and alloc.employee else None


def asset_out(asset: models.Asset, db=None) -> dict:
    return {
        "id": asset.id,
        "asset_tag": asset.asset_tag,
        "name": asset.name,
        "category_id": asset.category_id,
        "category_name": asset.category.name if asset.category else None,
        "department_id": asset.department_id,
        "department_name": asset.department.name if asset.department else None,
        "serial_number": asset.serial_number,
        "acquisition_date": asset.acquisition_date,
        "acquisition_cost": asset.acquisition_cost,
        "condition": asset.condition,
        "location": asset.location,
        "status": asset.status,
        "shared_flag": asset.shared_flag,
        "photo_url": asset.photo_url,
        "documents": asset.documents,
        "qr_value": asset.asset_tag,  # encoded client-side into a QR image
        "held_by": _active_holder(asset, db) if db is not None else None,
    }


def _is_overdue(alloc: models.Allocation) -> bool:
    if alloc.status != "Active" or not alloc.expected_return_date:
        return False
    return alloc.expected_return_date < date.today()


def _holder_label(alloc: models.Allocation) -> "str | None":
    if alloc.employee:
        return alloc.employee.full_name
    if alloc.department:
        return f"Dept: {alloc.department.name}"
    return None


def allocation_out(alloc: models.Allocation) -> dict:
    return {
        "id": alloc.id,
        "asset_id": alloc.asset_id,
        "asset_tag": alloc.asset.asset_tag if alloc.asset else None,
        "asset_name": alloc.asset.name if alloc.asset else None,
        "employee_id": alloc.employee_id,
        "employee_name": alloc.employee.full_name if alloc.employee else None,
        "department_id": alloc.department_id,
        "department_name": alloc.department.name if alloc.department else None,
        "holder": _holder_label(alloc),
        "allocated_date": alloc.allocated_date,
        "expected_return_date": alloc.expected_return_date,
        "returned_date": alloc.returned_date,
        "checkin_notes": alloc.checkin_notes,
        "status": alloc.status,
        "overdue": _is_overdue(alloc),
    }


def transfer_out(tr: models.TransferRequest) -> dict:
    return {
        "id": tr.id,
        "asset_id": tr.asset_id,
        "asset_tag": tr.asset.asset_tag if tr.asset else None,
        "from_employee_id": tr.from_employee_id,
        "from_employee_name": tr.from_employee.full_name if tr.from_employee else None,
        "to_employee_id": tr.to_employee_id,
        "to_employee_name": tr.to_employee.full_name if tr.to_employee else None,
        "reason": tr.reason,
        "status": tr.status,
    }


def booking_out(bk: models.Booking) -> dict:
    return {
        "id": bk.id,
        "asset_id": bk.asset_id,
        "resource_name": bk.resource_name,
        "booked_by": bk.booked_by,
        "start_time": bk.start_time,
        "end_time": bk.end_time,
        "purpose": bk.purpose,
        "status": bk.status,
    }


def maintenance_out(mr: models.MaintenanceRequest) -> dict:
    return {
        "id": mr.id,
        "asset_id": mr.asset_id,
        "asset_tag": mr.asset.asset_tag if mr.asset else None,
        "asset_name": mr.asset.name if mr.asset else None,
        "requester_name": mr.requester_name,
        "description": mr.description,
        "priority": mr.priority,
        "status": mr.status,
        "technician": mr.technician_name,
        "approved_by": mr.approved_by.full_name if mr.approved_by else None,
        "resolution_notes": mr.resolution_notes,
        "photo_url": mr.photo_url,
        "created_at": mr.created_at,
        "updated_at": mr.updated_at,
    }


def audit_item_out(item: models.AuditItem) -> dict:
    return {
        "id": item.id,
        "cycle_id": item.cycle_id,
        "asset_id": item.asset_id,
        "asset_tag": item.asset.asset_tag if item.asset else None,
        "asset_name": item.asset.name if item.asset else None,
        "result": item.result,
        "notes": item.notes,
        "checked_by": item.checked_by.full_name if item.checked_by else None,
        "checked_at": item.checked_at,
    }


def _audit_counts(cycle: models.AuditCycle) -> dict:
    total = len(cycle.items)
    verified = sum(1 for i in cycle.items if i.result == "Verified")
    missing = sum(1 for i in cycle.items if i.result == "Missing")
    damaged = sum(1 for i in cycle.items if i.result == "Damaged")
    pending = sum(1 for i in cycle.items if i.result == "Pending")
    checked = total - pending
    return {
        "total_items": total,
        "verified": verified,
        "missing": missing,
        "damaged": damaged,
        "pending": pending,
        "progress_pct": round(checked / total * 100) if total else 0,
    }


def audit_cycle_out(cycle: models.AuditCycle) -> dict:
    return {
        "id": cycle.id,
        "name": cycle.name,
        "scope_type": cycle.scope_type,
        "scope_value": cycle.scope_value,
        "start_date": cycle.start_date,
        "end_date": cycle.end_date,
        "status": cycle.status,
        "created_by": cycle.created_by.full_name if cycle.created_by else None,
        "created_at": cycle.created_at,
        "closed_at": cycle.closed_at,
        **_audit_counts(cycle),
    }


def notification_out(n: models.Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "message": n.message,
        "link": n.link,
        "is_read": n.is_read,
        "created_at": n.created_at,
    }


def activity_log_out(log: models.ActivityLog) -> dict:
    return {
        "id": log.id,
        "actor_id": log.actor_id,
        "actor_name": log.actor_name,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "summary": log.summary,
        "created_at": log.created_at,
    }


def audit_cycle_detail(cycle: models.AuditCycle) -> dict:
    data = audit_cycle_out(cycle)
    data["auditors"] = [
        {"id": a.auditor_id, "name": a.auditor.full_name if a.auditor else None}
        for a in cycle.assignments
    ]
    data["items"] = [
        audit_item_out(i) for i in sorted(cycle.items, key=lambda x: x.id)
    ]
    return data
