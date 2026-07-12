from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    head_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String(20), default="Active")

    head = relationship("Employee", foreign_keys=[head_id])
    parent = relationship("Department", remote_side=[id])


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(250), nullable=True)
    warranty_months = Column(Integer, nullable=True)  # optional category-specific field


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role = Column(String(50), default="Employee")
    status = Column(String(20), default="Active")
    reset_token = Column(String(100), nullable=True)  # demo password-reset token

    department = relationship("Department", foreign_keys=[department_id])


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    category_id = Column(Integer, ForeignKey("asset_categories.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    serial_number = Column(String(80), nullable=True)
    acquisition_date = Column(Date, nullable=True)
    acquisition_cost = Column(Integer, nullable=True)
    condition = Column(String(30), default="Good")
    location = Column(String(80), nullable=True)
    status = Column(String(30), default="Available")
    shared_flag = Column(Boolean, default=False)
    photo_url = Column(String(500), nullable=True)  # image URL for the asset
    documents = Column(Text, nullable=True)  # freeform links/notes to attached docs

    category = relationship("AssetCategory")
    department = relationship("Department")


class Allocation(Base):
    """Records who holds an asset. Target is an employee OR a department.
    status: Active | Returned."""

    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    allocated_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    allocated_date = Column(DateTime, default=_utcnow)
    expected_return_date = Column(Date, nullable=True)
    returned_date = Column(DateTime, nullable=True)
    checkin_notes = Column(Text, nullable=True)
    status = Column(String(20), default="Active")

    asset = relationship("Asset")
    employee = relationship("Employee", foreign_keys=[employee_id])
    department = relationship("Department", foreign_keys=[department_id])
    allocated_by = relationship("Employee", foreign_keys=[allocated_by_id])


class TransferRequest(Base):
    """Requested -> Approved/Rejected. On approval the asset is re-allocated."""

    __tablename__ = "transfer_requests"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    from_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    to_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    reason = Column(String(250), nullable=True)
    status = Column(String(20), default="Requested")
    created_at = Column(DateTime, default=_utcnow)

    asset = relationship("Asset")
    from_employee = relationship("Employee", foreign_keys=[from_employee_id])
    to_employee = relationship("Employee", foreign_keys=[to_employee_id])


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    resource_name = Column(String(120), nullable=False)
    booked_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    booked_by = Column(String(120), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    purpose = Column(String(250), nullable=True)
    status = Column(String(20), default="Upcoming")

    asset = relationship("Asset")


class MaintenanceRequest(Base):
    """Full repair workflow:
    Pending -> Approved/Rejected -> Technician Assigned -> In Progress -> Resolved.
    """

    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    requester_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    requester_name = Column(String(120), nullable=False)
    description = Column(String(250), nullable=False)
    priority = Column(String(20), default="Medium")
    status = Column(String(20), default="Pending")
    technician_name = Column(String(120), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    asset = relationship("Asset")
    approved_by = relationship("Employee", foreign_keys=[approved_by_id])


class AuditCycle(Base):
    """An audit campaign over a scoped set of assets. Open -> Closed."""

    __tablename__ = "audit_cycles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    scope_type = Column(String(20), default="All")  # Department | Location | All
    scope_value = Column(String(120), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), default="Open")  # Open | Closed
    created_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    closed_at = Column(DateTime, nullable=True)

    created_by = relationship("Employee", foreign_keys=[created_by_id])
    assignments = relationship(
        "AuditAssignment", back_populates="cycle", cascade="all, delete-orphan"
    )
    items = relationship("AuditItem", back_populates="cycle", cascade="all, delete-orphan")


class AuditAssignment(Base):
    """An auditor assigned to verify items in a cycle."""

    __tablename__ = "audit_assignments"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("audit_cycles.id"), nullable=False)
    auditor_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    cycle = relationship("AuditCycle", back_populates="assignments")
    auditor = relationship("Employee", foreign_keys=[auditor_id])


class AuditItem(Base):
    """One asset to be verified within a cycle."""

    __tablename__ = "audit_items"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("audit_cycles.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    result = Column(String(20), default="Pending")  # Pending | Verified | Missing | Damaged
    notes = Column(String(250), nullable=True)
    checked_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    checked_at = Column(DateTime, nullable=True)

    cycle = relationship("AuditCycle", back_populates="items")
    asset = relationship("Asset")
    checked_by = relationship("Employee", foreign_keys=[checked_by_id])


class ActivityLog(Base):
    """Immutable audit trail of who did what. Written by the events helper."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    actor_name = Column(String(120), nullable=False, default="System")
    action = Column(String(60), nullable=False)  # short code, e.g. "asset.allocated"
    entity_type = Column(String(40), nullable=True)  # e.g. "asset", "booking"
    entity_id = Column(Integer, nullable=True)
    summary = Column(String(300), nullable=False)  # human sentence
    created_at = Column(DateTime, default=_utcnow, index=True)

    actor = relationship("Employee", foreign_keys=[actor_id])


class Notification(Base):
    """A per-recipient message with optional deep-link into the frontend."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    type = Column(String(40), nullable=False)  # e.g. "allocation", "transfer", "overdue"
    message = Column(String(300), nullable=False)
    link = Column(String(120), nullable=True)  # optional frontend path
    is_read = Column(Boolean, default=False, index=True)
    dedupe_key = Column(String(120), nullable=True, index=True)  # prevents duplicate alerts
    created_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("Employee", foreign_keys=[user_id])
