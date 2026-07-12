from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AssetFlow API", version="0.1.0")

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


@app.post("/auth/login")
def login(payload: dict):
    if payload.get("email") and payload.get("password"):
        return {
            "access_token": "demo-token",
            "user": {
                "email": payload["email"],
                "role": "Admin",
                "name": "System Admin",
            },
        }
    return {"detail": "Invalid credentials"}
