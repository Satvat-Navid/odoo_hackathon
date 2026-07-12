from sqlalchemy import Column, Date, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    head_name = Column(String(100), nullable=True)
    status = Column(String(20), default="Active")


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(250), nullable=True)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role = Column(String(50), default="Employee")
    status = Column(String(20), default="Active")

    department = relationship("Department")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(50), nullable=False, unique=True)
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


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    resource_name = Column(String(120), nullable=False)
    booked_by = Column(String(120), nullable=False)
    start_time = Column(String(30), nullable=False)
    end_time = Column(String(30), nullable=False)
    status = Column(String(20), default="Upcoming")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    requester_name = Column(String(120), nullable=False)
    description = Column(String(250), nullable=False)
    priority = Column(String(20), default="Medium")
    status = Column(String(20), default="Pending")

    asset = relationship("Asset")
