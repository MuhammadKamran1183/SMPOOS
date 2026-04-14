# SMPOOS — Smart Maritime Port Operations System

SMPOOS is a lightweight, CSV-backed web application built for the CPS7002 (Software Design and Development) assignment. It provides a secure login, role-based administration tools, a monitoring dashboard, a notification engine, and basic analytics for port operations.

## Features

- Secure login with session handling and role-based access control (RBAC)
- Admin portal to manage operational data:
  - Port locations (zones/berths)
  - Internal routes (transit paths)
  - Vessel paths
  - Restricted areas
  - Crane outages
  - Berth allocations
- Real-time style dashboards:
  - Port monitoring (vessels, berth occupancy, environment, system health)
  - Analytics overview
- Notification engine:
  - Create notification rules and thresholds
  - View delivery audit trail and event logs
- CSV persistence (no database) for assignment compatibility

## Tech Stack

- Backend: Python (standard library HTTP server)
- Frontend: HTML + CSS + Vanilla JavaScript (served by the Python app)
- Storage: CSV files in `./data`

## Quick Start (Run Locally)

### Prerequisites

- Python 3 installed (recommended: 3.10+)
- Optional (for encryption features): `openssl` available on your system

### Start the server

From the repository root:

```bash
python3 app.py
```

Then open:

- http://127.0.0.1:8000/ (Login)

### Demo accounts

The login page includes demo buttons that autofill credentials:

- Admin: `user6@portauthority.com` / `admin123`
- Harbourmaster: `user19@portauthority.com` / `harbour123`
- Safety/Security: `user12@portauthority.com` / `safety123`

## Pages

- `/dashboard` — Management dashboard (widgets and summaries)
- `/monitoring` — Operational monitoring dashboard
- `/admin` — Admin operations (CRUD for operational datasets)
- `/notification-engine` — Configure notification rules and view audit trail
- `/analytics` — Analytics dashboards

Access to sections is controlled by RBAC; unavailable sections are disabled based on your role.

## Data (CSV Files)

SMPOOS stores data in CSV files under [data/](file:///Users/mymacos/Documents/GitHub/SMPOOS/data).

### Required assignment data sources

- `smpoos_locations.csv` — port zones/berths
- `smpoos_routes.csv` — internal routes / shipping lanes
- `smpoos_notifications.csv` — port notifications/alerts
- `smpoos_users.csv` — port personnel

### Additional app-managed CSVs

The app also maintains supporting CSVs (for authentication, monitoring, auditing, etc.), including:

- `smpoos_credentials.csv` (password hashes)
- `smpoos_vessel_paths.csv`
- `smpoos_restricted_areas.csv`
- `smpoos_crane_outages.csv`
- `smpoos_berth_allocations.csv`
- `smpoos_notification_rules.csv`
- `smpoos_notification_deliveries.csv`
- `smpoos_event_logs.csv`
- `smpoos_system_health.csv`
- `smpoos_environmental_updates.csv`
- `smpoos_compliance_audit.csv`

## Security Notes

- Authentication uses hashed passwords (PBKDF2-SHA256) stored in `smpoos_credentials.csv`.
- RBAC is enforced in the backend and reflected in the frontend UI.
- Optional HTTPS: provide TLS files via environment variables (see below).
- Optional encryption at rest for sensitive-record storage uses OpenSSL; set a strong `SMPOOS_SECRET_KEY`.

## Configuration (Environment Variables)

- `HOST` (default: `127.0.0.1`)
- `PORT` (default: `8000`)
- `SSL_CERT_FILE` / `SSL_KEY_FILE` (optional; enables HTTPS)
- `SMPOOS_SECRET_KEY` (optional; encryption passphrase; defaults to a dev secret)
- `OPENSSL_BIN` (optional; path to the `openssl` binary)

## Project Structure

- [app.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/app.py) — app bootstrap (wires services + starts server)
- [presentation/web_app.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation/web_app.py) — HTTP routing + static file serving
- [business_logic/port_data_service.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/business_logic/port_data_service.py) — domain logic, RBAC, API actions
- [data_access/csv_repository.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/data_access/csv_repository.py) — CSV persistence layer
- [frontend/](file:///Users/mymacos/Documents/GitHub/SMPOOS/frontend) — HTML/CSS/JS UI
- [data/](file:///Users/mymacos/Documents/GitHub/SMPOOS/data) — CSV datasets
- [security/secure_storage.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/security/secure_storage.py) — encryption helper (OpenSSL)

## Troubleshooting

- Login redirects back to `/login`:
  - Confirm you are using an active user account (`active` column in `smpoos_users.csv` must be `Yes`).
  - Use the built-in demo accounts from the login page.
- Encryption errors:
  - Ensure `openssl` is installed and accessible, or set `OPENSSL_BIN`.
  - Set `SMPOOS_SECRET_KEY` to a non-default value in production-like demos.
