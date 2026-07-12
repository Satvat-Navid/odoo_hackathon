"""Authentication & role-based access control helpers."""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# --- Config (dev defaults; override via env in production) ---------------------
SECRET_KEY = "assetflow-dev-secret-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12h sessions

# Role constants -- roles are ONLY ever assigned by an Admin (never at signup).
ROLE_ADMIN = "Admin"
ROLE_DEPARTMENT_HEAD = "Department Head"
ROLE_ASSET_MANAGER = "Asset Manager"
ROLE_EMPLOYEE = "Employee"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Employee:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(models.Employee).filter(models.Employee.email == email).first()
    if user is None or user.status != "Active":
        raise credentials_error
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory: allow only the given roles (Admin always allowed)."""

    def checker(current_user: models.Employee = Depends(get_current_user)) -> models.Employee:
        if current_user.role != ROLE_ADMIN and current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return checker


# Convenience dependencies
require_admin = require_roles(ROLE_ADMIN)
require_manager = require_roles(ROLE_ASSET_MANAGER, ROLE_DEPARTMENT_HEAD)
