from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import (
    ROLE_EMPLOYEE,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..serializers import employee_out

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.EmployeeOut, status_code=201)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Self-service signup — always creates a plain Employee. Roles are never
    self-assigned; only an Admin can promote from the Employee Directory."""
    existing = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = models.Employee(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=ROLE_EMPLOYEE,
        status="Active",
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee_out(employee)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if not employee or not verify_password(payload.password, employee.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if employee.status != "Active":
        raise HTTPException(status_code=403, detail="Account is inactive. Contact your admin.")

    token = create_access_token(subject=employee.email, role=employee.role)
    return {"access_token": token, "token_type": "bearer", "user": employee_out(employee)}


@router.get("/me", response_model=schemas.EmployeeOut)
def me(current_user: models.Employee = Depends(get_current_user)):
    return employee_out(current_user)
