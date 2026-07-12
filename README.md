# AssetFlow — Enterprise Asset & Resource Management

A role-based ERP for tracking assets and booking shared resources.
Stack: **React + Vite** (frontend) · **FastAPI + SQLAlchemy + SQLite** (backend) · **JWT + bcrypt** auth.

## Roles & access

Roles are **never self-assigned**. Signup always creates a plain **Employee**;
an **Admin** promotes people to **Department Head** or **Asset Manager** from the
Employee Directory. Access is enforced on every API route.

| Capability                        | Employee | Asset Manager / Dept Head | Admin |
|-----------------------------------|:--------:|:-------------------------:|:-----:|
| View dashboard, assets, bookings  | ✔ | ✔ | ✔ |
| Book resources, request transfers | ✔ | ✔ | ✔ |
| Register/edit assets, allocate    |   | ✔ | ✔ |
| Approve/reject transfers, returns |   | ✔ | ✔ |
| Organization Setup (master data)  |   |   | ✔ |

## Demo accounts

| Role          | Email                  | Password      |
|---------------|------------------------|---------------|
| Admin         | admin@assetflow.com    | `admin123`    |
| Asset Manager | priya@assetflow.com    | `password123` |
| Department Head | raj@assetflow.com    | `password123` |
| Employee      | meera@assetflow.com    | `password123` |

The predefined admin and demo data are seeded automatically on first run.

## Features (core 6)

1. **Login / Signup** — JWT auth; signup creates Employee only.
2. **Dashboard** — KPI cards, overdue vs. upcoming returns, lifecycle breakdown.
3. **Organization Setup** (admin) — Departments, Asset Categories, Employee Directory (role assignment).
4. **Asset Directory** — register with auto tag (AF-0001), search/filter, per-asset allocation history, full lifecycle (Available → Allocated → … → Disposed).
5. **Allocation & Transfer** — conflict rule blocks double-allocation and offers a transfer request; approval re-allocates; return flow with condition check-in.
6. **Resource Booking** — time-slot booking with overlap rejection (adjacent slots allowed).

## Run

### Backend (Python 3.9)

```bash
cd backend
python3.9 -m venv .venv           # if not already created
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API at http://127.0.0.1:8000 · interactive docs at http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173.

## Notes

- SQLite DB (`backend/assetflow.db`) is created and seeded on first startup. Delete it to reset to fresh demo data.
- `bcrypt` is pinned to `4.0.1` for compatibility with `passlib` 1.7.4.
- CORS is open to the Vite dev origin (`localhost:5173`).
