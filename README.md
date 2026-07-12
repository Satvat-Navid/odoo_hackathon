# AssetFlow

A React + FastAPI + SQLite starter for the AssetFlow ERP concept.

## Project structure

- backend/ - FastAPI API and SQLite-backed starter app
- frontend/ - React + Vite frontend
- README.md - setup and run instructions

## Backend

1. Open PowerShell in the backend folder.
2. Create or activate the virtual environment.
3. Install dependencies.
4. Start the API server.

Example:

```powershell
cd backend
py -3.9 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install fastapi uvicorn pydantic
python -m uvicorn app.simple_main:app --app-dir . --host 127.0.0.1 --port 8000
```

The API exposes:
- GET /health
- POST /auth/login

## Frontend

1. Open PowerShell in the frontend folder.
2. Install dependencies.
3. Start the dev server.

Example:

```powershell
cd frontend
npm install
npm run dev
```

Then open http://127.0.0.1:5173.

## Current milestone

The starter includes:
- a backend API shell with an auth login route
- a React app with a login page and a protected dashboard page
- a simple login flow that redirects to the dashboard after successful authentication

Use the demo credentials:
- Email: any non-empty value
- Password: any non-empty value

The next step will be to expand the app with the full business modules and database models.
use python3.9