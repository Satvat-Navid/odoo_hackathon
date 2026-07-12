# AssetFlow — Enterprise Asset & Resource Management

A role-based ERP for tracking assets and booking shared resources.
Stack: **React + Vite** (frontend) · **FastAPI + SQLAlchemy + SQLite** (backend) · **JWT + bcrypt** auth.

## Roles & access

Roles are **never self-assigned**. Signup always creates a plain **Employee**;
an **Admin** promotes people to **Department Head** or **Asset Manager** from the
Employee Directory. Access is enforced on every API route.

| Capability                        | Employee | Asset Manager | Dept Head | Admin |
|-----------------------------------|:--------:|:-------------:|:---------:|:-----:|
| View dashboard, assets, bookings  | ✔ | ✔ | ✔ | ✔ |
| Book resources, request transfers | ✔ | ✔ | ✔ | ✔ |
| Reschedule / cancel own bookings  | ✔ | ✔ | ✔ | ✔ |
| Receive notifications             | ✔ | ✔ | ✔ | ✔ |
| Register/edit assets, allocate    |   | ✔ | ✔ (own dept) | ✔ |
| Approve/reject transfers, returns |   | ✔ | ✔ (own dept) | ✔ |
| Reports & Analytics               |   | ✔ | ✔ | ✔ |
| Activity Log                      |   | ✔ | ✔ | ✔ |
| Organization Setup (master data)  |   |   |   | ✔ |

**Department Head scoping:** a Department Head sees and approves allocations &
transfers only for **their own department**. Asset Managers and Admins retain
org-wide access.

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
6. **Resource Booking** — time-slot booking with overlap rejection (adjacent slots allowed), plus **reschedule** and pre-slot **reminder** alerts.

## Features (Part 1 — Maintenance & Audit)

7. **Maintenance** — full repair workflow (Pending → Approved/Rejected → Technician Assigned → In Progress → Resolved); requesters are notified at each decision.
8. **Asset Audit** — audit cycles scoped by department/location/all; assigned auditors record Verified/Missing/Damaged; discrepancies alert admins and apply to assets on close.

## Features (Part 2 — Analytics, Logs & Notifications)

9. **Reports & Analytics** (Managers/Admin) — headline KPI cards plus dependency-free charts:
   - **Asset utilization** — days allocated & times allocated per asset; most-used vs. idle.
   - **Maintenance frequency** — grouped by asset and by category.
   - **Due / at-risk maintenance** — flagged by warranty age, repeated repairs, poor condition, or currently under maintenance.
   - **Department allocation** — currently-allocated assets per department.
   - **Booking heatmap** — weekday × hour peak-demand grid.
   - Every panel has a client-side **Export CSV** button.
10. **Activity Log & Notifications** —
    - **Activity Log** (`/activity`, Managers/Admin): filterable trail of who did what, when.
    - **Notifications**: a bell with unread count and a dropdown. Users are notified on asset allocation, transfer approval/rejection, booking confirm/cancel/reschedule, maintenance approve/reject/resolve, audit discrepancies (admins), and role changes. **Overdue-return** and **booking-reminder** alerts are generated on-fetch (deduped, no scheduler).

## Additional capabilities

- **Forgot / reset password** — `POST /auth/forgot-password` returns a one-time `reset_token` (demo-safe: it would be emailed in production), then `POST /auth/reset-password` sets a new password. Reachable from the login screen via **Forgot password?**.
- **Department allocation** — an asset can be allocated to a **department** (not only an employee); the department head is notified.
- **Asset media & QR** — assets carry an optional **photo URL** and **documents** field; the **Details** dialog shows a **QR code** of the asset tag.

## New endpoints (Part 2)

```
GET  /notifications                 (own; ?unread_only=true)
GET  /notifications/unread-count
POST /notifications/{id}/read
POST /notifications/read-all
GET  /activity-logs                 (manager/admin; ?entity_type= &actor_id= &limit=)
GET  /reports/summary
GET  /reports/asset-utilization
GET  /reports/maintenance-frequency
GET  /reports/due-maintenance
GET  /reports/department-allocation
GET  /reports/booking-heatmap
POST /bookings/{id}/reschedule
POST /auth/forgot-password
POST /auth/reset-password
```

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

- SQLite DB (`backend/assetflow.db`) is created and seeded on first startup. Delete it to reset to fresh demo data — **required after pulling Part 2**, since new tables/columns (notifications, activity logs, allocation department target, asset photo/QR) are added. The seed now includes historical allocations, spread-out bookings, and sample notifications so Reports render non-empty.
- `bcrypt` is pinned to `4.0.1` for compatibility with `passlib` 1.7.4.
- Code targets **Python 3.9** (uses `typing.Optional`, never `X | None` in evaluated annotations).
- Reports charts are **dependency-free** (inline CSS bars + SVG-style grid); the asset QR uses a public QR image endpoint keyed on the asset tag.
- CORS is open to the Vite dev origin (`localhost:5173`).
