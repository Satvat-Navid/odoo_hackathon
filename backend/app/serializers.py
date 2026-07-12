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
        "held_by": _active_holder(asset, db) if db is not None else None,
    }


def _is_overdue(alloc: models.Allocation) -> bool:
    if alloc.status != "Active" or not alloc.expected_return_date:
        return False
    return alloc.expected_return_date < date.today()


def allocation_out(alloc: models.Allocation) -> dict:
    return {
        "id": alloc.id,
        "asset_id": alloc.asset_id,
        "asset_tag": alloc.asset.asset_tag if alloc.asset else None,
        "asset_name": alloc.asset.name if alloc.asset else None,
        "employee_id": alloc.employee_id,
        "employee_name": alloc.employee.full_name if alloc.employee else None,
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
