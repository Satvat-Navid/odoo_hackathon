from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# --- Auth ---------------------------------------------------------------------
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "EmployeeOut"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Demo-safe: the reset token is returned directly (would be emailed in prod)."""
    message: str
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# --- Departments --------------------------------------------------------------
class DepartmentCreate(BaseModel):
    name: str
    head_id: Optional[int] = None
    parent_id: Optional[int] = None
    status: str = "Active"


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    head_id: Optional[int] = None
    parent_id: Optional[int] = None
    status: Optional[str] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    head_id: Optional[int] = None
    head_name: Optional[str] = None
    parent_id: Optional[int] = None
    status: str

    class Config:
        from_attributes = True


# --- Asset categories ---------------------------------------------------------
class AssetCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    warranty_months: Optional[int] = None


class AssetCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    warranty_months: Optional[int] = None


class AssetCategoryOut(AssetCategoryCreate):
    id: int

    class Config:
        from_attributes = True


# --- Employees ----------------------------------------------------------------
class EmployeeOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    role: str
    status: str

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = "password123"
    department_id: Optional[int] = None
    role: str = "Employee"
    status: str = "Active"


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None
    status: Optional[str] = None


# --- Assets -------------------------------------------------------------------
class AssetCreate(BaseModel):
    name: str
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[int] = None
    condition: str = "Good"
    location: Optional[str] = None
    shared_flag: bool = False
    photo_url: Optional[str] = None
    documents: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    shared_flag: Optional[bool] = None
    photo_url: Optional[str] = None
    documents: Optional[str] = None


class AssetOut(BaseModel):
    id: int
    asset_tag: str
    name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    serial_number: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[int] = None
    condition: str
    location: Optional[str] = None
    status: str
    shared_flag: bool
    photo_url: Optional[str] = None
    documents: Optional[str] = None
    qr_value: Optional[str] = None  # asset tag encoded for a QR code
    held_by: Optional[str] = None

    class Config:
        from_attributes = True


# --- Allocations & transfers --------------------------------------------------
class AllocationCreate(BaseModel):
    asset_id: int
    employee_id: Optional[int] = None  # target an employee...
    department_id: Optional[int] = None  # ...or a department (exactly one)
    expected_return_date: Optional[date] = None


class AllocationReturn(BaseModel):
    checkin_notes: Optional[str] = None
    condition: Optional[str] = None


class AllocationOut(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    holder: Optional[str] = None  # employee name or "Dept: X"
    allocated_date: Optional[datetime] = None
    expected_return_date: Optional[date] = None
    returned_date: Optional[datetime] = None
    checkin_notes: Optional[str] = None
    status: str
    overdue: bool = False

    class Config:
        from_attributes = True


class TransferCreate(BaseModel):
    asset_id: int
    to_employee_id: int
    reason: Optional[str] = None


class TransferOut(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    from_employee_id: Optional[int] = None
    from_employee_name: Optional[str] = None
    to_employee_id: int
    to_employee_name: Optional[str] = None
    reason: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


# --- Bookings -----------------------------------------------------------------
class BookingCreate(BaseModel):
    asset_id: Optional[int] = None
    resource_name: str
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    asset_id: Optional[int] = None
    resource_name: str
    booked_by: str
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


# --- Maintenance --------------------------------------------------------------
class MaintenanceCreate(BaseModel):
    asset_id: int
    description: str
    priority: str = "Medium"
    photo_url: Optional[str] = None


class MaintenanceAssign(BaseModel):
    technician: str


class MaintenanceResolve(BaseModel):
    resolution_notes: Optional[str] = None


class MaintenanceOut(BaseModel):
    id: int
    asset_id: Optional[int] = None
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    requester_name: str
    description: str
    priority: str
    status: str
    technician: Optional[str] = None
    approved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Asset audit --------------------------------------------------------------
class AuditCycleCreate(BaseModel):
    name: str
    scope_type: str = "All"  # Department | Location | All
    scope_value: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AuditorsAssign(BaseModel):
    auditor_ids: list[int]


class AuditItemUpdate(BaseModel):
    result: str  # Verified | Missing | Damaged | Pending
    notes: Optional[str] = None


class AuditItemOut(BaseModel):
    id: int
    cycle_id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    result: str
    notes: Optional[str] = None
    checked_by: Optional[str] = None
    checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditCycleOut(BaseModel):
    id: int
    name: str
    scope_type: str
    scope_value: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    total_items: int = 0
    verified: int = 0
    missing: int = 0
    damaged: int = 0
    pending: int = 0
    progress_pct: int = 0

    class Config:
        from_attributes = True


# --- Booking reschedule -------------------------------------------------------
class BookingReschedule(BaseModel):
    start_time: datetime
    end_time: datetime


# --- Notifications ------------------------------------------------------------
class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UnreadCountOut(BaseModel):
    unread: int


# --- Activity log -------------------------------------------------------------
class ActivityLogOut(BaseModel):
    id: int
    actor_id: Optional[int] = None
    actor_name: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    summary: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
