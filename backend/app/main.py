from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .seed import seed
from .api.auth import router as auth_router
from .api.organization import router as organization_router
from .api.assets import router as assets_router
from .api.allocations import router as allocations_router
from .api.bookings import router as bookings_router
from .api.dashboard import router as dashboard_router
from .api.maintenance import router as maintenance_router
from .api.audit import router as audit_router
from .api.notifications import router as notifications_router
from .api.reports import router as reports_router

Base.metadata.create_all(bind=engine)

# Seed predefined admin + demo data on an empty database.
with SessionLocal() as _db:
    seed(_db)

app = FastAPI(title="AssetFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(assets_router)
app.include_router(allocations_router)
app.include_router(bookings_router)
app.include_router(dashboard_router)
app.include_router(maintenance_router)
app.include_router(audit_router)
app.include_router(notifications_router)
app.include_router(reports_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
