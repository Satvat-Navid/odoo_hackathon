"""Seed a predefined Admin plus demo master data. Runs once on empty DB."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from . import models
from .security import (
    ROLE_ADMIN,
    ROLE_ASSET_MANAGER,
    ROLE_DEPARTMENT_HEAD,
    ROLE_EMPLOYEE,
    hash_password,
)

# Predefined admin — the only account not created through signup.
ADMIN_EMAIL = "admin@assetflow.com"
ADMIN_PASSWORD = "admin123"
DEMO_PASSWORD = "password123"


def seed(db: Session) -> None:
    if db.query(models.Employee).first():
        return  # already seeded

    # Departments
    it = models.Department(name="IT", status="Active")
    facilities = models.Department(name="Facilities", status="Active")
    ops = models.Department(name="Operations", status="Active")
    db.add_all([it, facilities, ops])
    db.flush()

    # Employees (roles assigned here, never at signup)
    admin = models.Employee(
        full_name="System Admin", email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD), role=ROLE_ADMIN,
        department_id=it.id, status="Active",
    )
    priya = models.Employee(
        full_name="Priya Sharma", email="priya@assetflow.com",
        password_hash=hash_password(DEMO_PASSWORD), role=ROLE_ASSET_MANAGER,
        department_id=it.id, status="Active",
    )
    raj = models.Employee(
        full_name="Raj Patel", email="raj@assetflow.com",
        password_hash=hash_password(DEMO_PASSWORD), role=ROLE_DEPARTMENT_HEAD,
        department_id=ops.id, status="Active",
    )
    meera = models.Employee(
        full_name="Meera Nair", email="meera@assetflow.com",
        password_hash=hash_password(DEMO_PASSWORD), role=ROLE_EMPLOYEE,
        department_id=facilities.id, status="Active",
    )
    db.add_all([admin, priya, raj, meera])
    db.flush()

    it.head_id = priya.id
    ops.head_id = raj.id

    # Categories
    electronics = models.AssetCategory(
        name="Electronics", description="Laptops, monitors, phones", warranty_months=24
    )
    furniture = models.AssetCategory(name="Furniture", description="Desks, chairs, cabinets")
    vehicles = models.AssetCategory(name="Vehicles", description="Company cars & vans")
    rooms = models.AssetCategory(name="Rooms", description="Bookable meeting rooms")
    db.add_all([electronics, furniture, vehicles, rooms])
    db.flush()

    # Assets
    assets = [
        models.Asset(asset_tag="AF-0001", name="Dell Latitude 7440", category_id=electronics.id,
                     department_id=it.id, serial_number="DL7440-001", condition="Good",
                     location="HQ - Floor 3", status="Available", acquisition_cost=1200,
                     acquisition_date=date(2024, 3, 12)),
        models.Asset(asset_tag="AF-0002", name="MacBook Pro 14", category_id=electronics.id,
                     department_id=it.id, serial_number="MBP14-114", condition="Good",
                     location="HQ - Floor 3", status="Available", acquisition_cost=2400,
                     acquisition_date=date(2024, 6, 1)),
        models.Asset(asset_tag="AF-0003", name="Ergonomic Chair", category_id=furniture.id,
                     department_id=facilities.id, condition="Fair", location="HQ - Floor 2",
                     status="Available", acquisition_cost=300),
        models.Asset(asset_tag="AF-0004", name="Toyota Hiace Van", category_id=vehicles.id,
                     department_id=ops.id, serial_number="VIN-HIACE-22", condition="Good",
                     location="Parking Bay 1", status="Available", acquisition_cost=32000),
        models.Asset(asset_tag="AF-0005", name="Meeting Room B2", category_id=rooms.id,
                     department_id=facilities.id, location="HQ - Floor 1", status="Available",
                     shared_flag=True),
        models.Asset(asset_tag="AF-0006", name="Projector Epson X50", category_id=electronics.id,
                     department_id=it.id, condition="Good", location="Store Room",
                     status="Available", shared_flag=True, acquisition_cost=650),
    ]
    db.add_all(assets)
    db.flush()

    # An active (overdue) allocation to make the dashboard meaningful
    laptop = assets[1]  # MacBook -> Priya, overdue
    laptop.status = "Allocated"
    db.add(models.Allocation(
        asset_id=laptop.id, employee_id=priya.id, allocated_by_id=admin.id,
        expected_return_date=date.today() - timedelta(days=2), status="Active",
    ))

    # A sample booking for Room B2
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    db.add(models.Booking(
        asset_id=assets[4].id, resource_name="Meeting Room B2", booked_by_id=raj.id,
        booked_by=raj.full_name, start_time=start, end_time=start + timedelta(hours=1),
        purpose="Sprint planning", status="Upcoming",
    ))

    # Maintenance requests in different workflow states
    db.add(models.MaintenanceRequest(
        asset_id=assets[2].id, requester_name=meera.full_name,
        description="Chair hydraulics failing, seat drops randomly.",
        priority="High", status="Pending",
    ))
    projector = assets[5]  # Approved -> asset goes Under Maintenance
    projector.status = "Under Maintenance"
    db.add(models.MaintenanceRequest(
        asset_id=projector.id, requester_name=raj.full_name,
        description="Projector lamp flickering during presentations.",
        priority="Medium", status="Approved", approved_by_id=priya.id,
    ))

    # An Open audit cycle scoped to IT, with an assigned auditor + generated items
    cycle = models.AuditCycle(
        name="Q3 IT Asset Audit", scope_type="Department", scope_value="IT",
        start_date=date.today(), end_date=date.today() + timedelta(days=14),
        status="Open", created_by_id=admin.id,
    )
    db.add(cycle)
    db.flush()
    db.add(models.AuditAssignment(cycle_id=cycle.id, auditor_id=meera.id))
    for asset in assets:
        if asset.department_id == it.id:
            db.add(models.AuditItem(cycle_id=cycle.id, asset_id=asset.id, result="Pending"))

    db.commit()
