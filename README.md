# SMPOOS — Smart Maritime Port Operations System

SMPOOS is a CSV-backed port operations web application built with Python and Dash. It provides role-based access, operational dashboards, an admin workspace, a notification engine, and analytics for port activity.

## Current Stack

- UI and routing: Dash + Flask
- Charts: Plotly, Seaborn, Matplotlib
- Storage: CSV files in `data/`
- Entry point: `app.py`
- Main app module: `dash_app.py`

## What The App Includes

- Secure login with session-based authentication
- Role-based access control for each page
- Management dashboard
- Port monitoring dashboard
- Admin CRUD tools for operational data
- Notification engine with live updates
- Analytics report builder with graphs and tables

## Run Locally

### Requirements

- Python 3.10+

### Install

```bash
python3 -m pip install -r requirements.txt
```

### Start The App
python3 app.py

Open:

- [http://127.0.0.1:8050/login](http://127.0.0.1:8050/login)

## Demo Accounts

- Admin: `user6@portauthority.com` / `admin123`
- Harbourmaster: `user19@portauthority.com` / `harbour123`
- Safety/Security: `user12@portauthority.com` / `safety123`

## Pages

- "/login" — sign in page
- "/dashboard" — management dashboard
- "/monitoring" — operational monitoring
- "/admin" — CRUD management for port datasets
- "/notification-engine" — notification rules, deliveries, notifications, and event logs
- "/analytics" — report builder with filters, summary, graphs, and recommendations

Access is permission-based, so available pages depend on the logged-in user role.

## Architecture

This project follows a layered architecture:

- Presentation layer: "dash_app.py" and "presentation/"
- Business logic layer: "business_logic/"
- Data access layer: "data_access/"
- Storage layer: "database/"
- Domain models: "model/"

Typical flow:

- Dash callbacks and page layouts call the service layer
- The service layer applies permissions and business rules
- The repository reads and writes CSV-backed records
- The CSV database utility lives in "data_access/"

## Project Structure

- [app.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/app.py) — local startup wrapper
- [dash_app.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/dash_app.py) — Dash app, callbacks, routing, shared UI helpers, and admin page
- [presentation](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation) — presentation layer utilities (theme/components/charts + page layouts)
- [business_logic](file:///Users/mymacos/Documents/GitHub/SMPOOS/business_logic) — service layer and core application logic
- [data_access](file:///Users/mymacos/Documents/GitHub/SMPOOS/data_access) — repository layer for records
- [database](file:///Users/mymacos/Documents/GitHub/SMPOOS/database) — CSV file access utilities
- [model](file:///Users/mymacos/Documents/GitHub/SMPOOS/model) — domain models
- [data](file:///Users/mymacos/Documents/GitHub/SMPOOS/data) — CSV datasets used by the app

### `presentation/screens/`

- [login_screen.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation/screens/login_screen.py) — login page layout
- [dashboard_screen.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation/screens/dashboard_screen.py) — dashboard layout
- [monitoring_screen.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation/screens/monitoring_screen.py) — monitoring layout
- [notification_screen.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation/screens/notification_screen.py) — notification engine layout
- [analytics_screen.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/presentation/screens/analytics_screen.py) — analytics layout and graph builders

### Important Note

- The "Admin" page is still defined directly in [dash_app.py](file:///Users/mymacos/Documents/GitHub/SMPOOS/dash_app.py).
- Other major pages are rendered through `presentation/screens/`.

## Data Files

Core CSV files include:

- smpoos_locations.csv
- smpoos_routes.csv
- smpoos_notifications.csv
- smpoos_users.csv
- smpoos_vessel_paths.csv
- smpoos_restricted_areas.csv
- smpoos_crane_outages.csv
- smpoos_berth_allocations.csv
- smpoos_notification_rules.csv
- smpoos_notification_deliveries.csv
- smpoos_event_logs.csv
- smpoos_system_health.csv
- smpoos_environmental_updates.csv
- smpoos_credentials.csv

Additional assignment/supporting CSVs are also present under [data](file:///Users/mymacos/Documents/GitHub/SMPOOS/data).

## Security And Sessions

- Passwords are stored as PBKDF2-SHA256 hashes in "smpoos_credentials.csv"
- Access is enforced through backend permission checks
- Flask session storage is used for login state

## Environment Variables

- "HOST" — default "127.0.0.1"
- "PORT" — default "8050"
- "SMPOOS_SECRET_KEY" — optional Flask session secret

## Troubleshooting

- Login keeps redirecting to "/login"
  - Check that the user exists and is active in "smpoos_users.csv"
  - Use one of the built-in demo accounts
- App does not start
  - Confirm dependencies are installed from "requirements.txt"
  - Confirm port "8050"is not already in use
