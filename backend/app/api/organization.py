from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..events import log_activity, notify
from ..security import (
    ROLE_ADMIN,
    ROLE_ASSET_MANAGER,
    ROLE_DEPARTMENT_HEAD,
    ROLE_EMPLOYEE,
    get_current_user,
    hash_password,
    require_admin,
)
from ..serializers import category_out, department_out, employee_out

router = APIRouter(tags=["organization"])

ASSIGNABLE_ROLES = {ROLE_EMPLOYEE, ROLE_DEPARTMENT_HEAD, ROLE_ASSET_MANAGER, ROLE_ADMIN}


# --- Departments --------------------------------------------------------------
@router.get("/departments", response_model=list[schemas.DepartmentOut])
def list_departments(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [department_out(d) for d in db.query(models.Department).all()]


@router.post("/departments", response_model=schemas.DepartmentOut, status_code=201)
def create_department(
    payload: schemas.DepartmentCreate, db: Session = Depends(get_db), _=Depends(require_admin)
):
    if db.query(models.Department).filter(models.Department.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Department name already exists")
    dep = models.Department(**payload.model_dump())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return department_out(dep)


@router.patch("/departments/{dep_id}", response_model=schemas.DepartmentOut)
def update_department(
    dep_id: int,
    payload: schemas.DepartmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    dep = db.get(models.Department, dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(dep, key, value)
    db.commit()
    db.refresh(dep)
    return department_out(dep)


@router.delete("/departments/{dep_id}", status_code=204)
def delete_department(dep_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    dep = db.get(models.Department, dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
    if db.query(models.Employee).filter(models.Employee.department_id == dep_id).first():
        raise HTTPException(status_code=409, detail="Department has employees. Reassign them first.")
    if db.query(models.Asset).filter(models.Asset.department_id == dep_id).first():
        raise HTTPException(status_code=409, detail="Department has assets. Reassign them first.")
    if db.query(models.Department).filter(models.Department.parent_id == dep_id).first():
        raise HTTPException(status_code=409, detail="Department has sub-departments. Remove them first.")
    db.delete(dep)
    db.commit()
    return Response(status_code=204)


# --- Asset categories ---------------------------------------------------------
@router.get("/asset-categories", response_model=list[schemas.AssetCategoryOut])
def list_categories(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [category_out(c) for c in db.query(models.AssetCategory).all()]


@router.post("/asset-categories", response_model=schemas.AssetCategoryOut, status_code=201)
def create_category(
    payload: schemas.AssetCategoryCreate, db: Session = Depends(get_db), _=Depends(require_admin)
):
    if db.query(models.AssetCategory).filter(models.AssetCategory.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = models.AssetCategory(**payload.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return category_out(cat)


@router.patch("/asset-categories/{cat_id}", response_model=schemas.AssetCategoryOut)
def update_category(
    cat_id: int,
    payload: schemas.AssetCategoryUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    cat = db.get(models.AssetCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return category_out(cat)


@router.delete("/asset-categories/{cat_id}", status_code=204)
def delete_category(cat_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    cat = db.get(models.AssetCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if db.query(models.Asset).filter(models.Asset.category_id == cat_id).first():
        raise HTTPException(status_code=409, detail="Category is in use by assets. Reassign them first.")
    db.delete(cat)
    db.commit()
    return Response(status_code=204)


# --- Employee directory -------------------------------------------------------
@router.get("/employees", response_model=list[schemas.EmployeeOut])
def list_employees(db: Session = Depends(get_db), current=Depends(get_current_user)):
    if current.role != ROLE_EMPLOYEE:
        employees = db.query(models.Employee).all()
    else:
        employees = [current]
    return [employee_out(e) for e in employees]


@router.post("/employees", response_model=schemas.EmployeeOut, status_code=201)
def create_employee(
    payload: schemas.EmployeeCreate, db: Session = Depends(get_db), _=Depends(require_admin)
):
    """Admin adds a directory entry directly, with a role assigned up front."""
    if db.query(models.Employee).filter(models.Employee.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if payload.role not in ASSIGNABLE_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    emp = models.Employee(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        department_id=payload.department_id,
        role=payload.role,
        status=payload.status,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return employee_out(emp)


@router.patch("/employees/{emp_id}", response_model=schemas.EmployeeOut)
def update_employee(
    emp_id: int,
    payload: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    current=Depends(require_admin),
):
    """The ONLY place roles are assigned — Admin promotes/updates directory entries."""
    emp = db.get(models.Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    data = payload.model_dump(exclude_unset=True)
    if "role" in data and data["role"] not in ASSIGNABLE_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    role_changed = "role" in data and data["role"] != emp.role
    new_role = data.get("role")
    for key, value in data.items():
        setattr(emp, key, value)
    if role_changed:
        log_activity(db, current, "employee.role_changed", "employee", emp.id,
                     f"{current.full_name} changed {emp.full_name}'s role to {new_role}")
        notify(db, emp.id, "role",
               f"Your role was updated to {new_role}.", "/dashboard")
    db.commit()
    db.refresh(emp)
    return employee_out(emp)


@router.delete("/employees/{emp_id}", status_code=204)
def delete_employee(
    emp_id: int, db: Session = Depends(get_db), current=Depends(require_admin)
):
    emp = db.get(models.Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.id == current.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    active = (
        db.query(models.Allocation)
        .filter(models.Allocation.employee_id == emp_id, models.Allocation.status == "Active")
        .first()
    )
    if active:
        raise HTTPException(status_code=409, detail="Employee still holds assets. Return them first.")
    if db.query(models.Department).filter(models.Department.head_id == emp_id).first():
        raise HTTPException(status_code=409, detail="Employee heads a department. Reassign the head first.")
    db.delete(emp)
    db.commit()
    return Response(status_code=204)
