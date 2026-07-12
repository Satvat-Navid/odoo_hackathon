from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .api.auth import router as auth_router
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AssetFlow API", version="0.1.0")
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/departments", response_model=schemas.DepartmentOut)
def create_department(payload: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    department = models.Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@app.get("/departments", response_model=list[schemas.DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).all()


@app.post("/asset-categories", response_model=schemas.AssetCategoryOut)
def create_category(payload: schemas.AssetCategoryCreate, db: Session = Depends(get_db)):
    category = models.AssetCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@app.get("/asset-categories", response_model=list[schemas.AssetCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.AssetCategory).all()


@app.post("/employees", response_model=schemas.EmployeeOut)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    employee = models.Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@app.get("/employees", response_model=list[schemas.EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return db.query(models.Employee).all()


@app.post("/assets", response_model=schemas.AssetOut)
def create_asset(payload: schemas.AssetCreate, db: Session = Depends(get_db)):
    asset = models.Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@app.get("/assets", response_model=list[schemas.AssetOut])
def list_assets(db: Session = Depends(get_db)):
    return db.query(models.Asset).all()


@app.post("/bookings", response_model=schemas.BookingOut)
def create_booking(payload: schemas.BookingCreate, db: Session = Depends(get_db)):
    booking = models.Booking(**payload.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/bookings", response_model=list[schemas.BookingOut])
def list_bookings(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()


@app.post("/maintenance-requests", response_model=schemas.MaintenanceRequestOut)
def create_maintenance_request(payload: schemas.MaintenanceRequestCreate, db: Session = Depends(get_db)):
    request = models.MaintenanceRequest(**payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@app.get("/maintenance-requests", response_model=list[schemas.MaintenanceRequestOut])
def list_maintenance_requests(db: Session = Depends(get_db)):
    return db.query(models.MaintenanceRequest).all()
