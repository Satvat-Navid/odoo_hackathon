from datetime import date
from typing import Optional
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    head_name: Optional[str] = None
    status: str = "Active"


class DepartmentOut(DepartmentCreate):
    id: int


class AssetCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class AssetCategoryOut(AssetCategoryCreate):
    id: int


class EmployeeCreate(BaseModel):
    full_name: str
    email: str
    department_id: Optional[int] = None
    role: str = "Employee"
    status: str = "Active"


class EmployeeOut(EmployeeCreate):
    id: int


class AssetCreate(BaseModel):
    asset_tag: str
    name: str
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[int] = None
    condition: str = "Good"
    location: Optional[str] = None
    status: str = "Available"
    shared_flag: bool = False


class AssetOut(AssetCreate):
    id: int


class BookingCreate(BaseModel):
    resource_name: str
    booked_by: str
    start_time: str
    end_time: str
    status: str = "Upcoming"


class BookingOut(BookingCreate):
    id: int


class MaintenanceRequestCreate(BaseModel):
    asset_id: Optional[int] = None
    requester_name: str
    description: str
    priority: str = "Medium"
    status: str = "Pending"


class MaintenanceRequestOut(MaintenanceRequestCreate):
    id: int
