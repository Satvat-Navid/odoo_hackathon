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

    category = relationship("AssetCategory")
    department = relationship("Department")


class Allocation(Base):
    """Records who holds an asset. status: Active | Returned."""

    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    allocated_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    allocated_date = Column(DateTime, default=_utcnow)
    expected_return_date = Column(Date, nullable=True)
    returned_date = Column(DateTime, nullable=True)
    checkin_notes = Column(Text, nullable=True)
    status = Column(String(20), default="Active")

    asset = relationship("Asset")
    employee = relationship("Employee", foreign_keys=[employee_id])
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
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    requester_name = Column(String(120), nullable=False)
    description = Column(String(250), nullable=False)
    priority = Column(String(20), default="Medium")
    status = Column(String(20), default="Pending")
    created_at = Column(DateTime, default=_utcnow)

    asset = relationship("Asset")
