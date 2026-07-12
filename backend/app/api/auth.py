from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if payload.password != "password123":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": "demo-token",
        "user": {
            "id": employee.id,
            "email": employee.email,
            "role": employee.role,
            "name": employee.full_name,
        },
    }


@router.post("/register")
def register(payload: AuthRequest, db: Session = Depends(get_db)):
    existing = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = models.Employee(full_name=payload.email.split('@')[0], email=payload.email, role="Employee")
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return {"message": "User registered successfully", "user_id": employee.id}
