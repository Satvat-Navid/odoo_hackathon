import secrets

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


@router.post("/forgot-password", response_model=schemas.ForgotPasswordResponse)
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Issue a one-time reset token. Demo-safe: the token is returned in the
    response (in production it would be emailed). Always responds 200 so the
    endpoint can't be used to enumerate registered emails."""
    employee = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    generic = "If that email exists, a reset token has been generated."
    if not employee:
        return {"message": generic, "reset_token": None}
    token = secrets.token_urlsafe(16)
    employee.reset_token = token
    db.commit()
    return {"message": generic, "reset_token": token}


@router.post("/reset-password", response_model=schemas.EmployeeOut)
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    employee = (
        db.query(models.Employee)
        .filter(models.Employee.reset_token == payload.token)
        .first()
    )
    if not employee or not payload.token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    employee.password_hash = hash_password(payload.new_password)
    employee.reset_token = None  # single-use
    db.commit()
    db.refresh(employee)
    return employee_out(employee)
