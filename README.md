# MVHS Medication Expiration Tracker

A Django 5 application for MVHS Medical Group offices to manage medication inventory, track expiration dates, and coordinate office-level stock.

## Features

- Role-aware dashboards for administrators and staff
- Office catalog management with medication assignments and per-lot tracking
- Expiring and expired reporting with CSV exports and daily digest emails
- REST API (session-authenticated) for offices, medications, stock, lots, and reports
- Tailwind-powered UI delivered via HTMX-friendly server-rendered templates

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run build:css
python manage.py migrate
python manage.py loaddata fixtures/seed.json
python manage.py runserver
```

Visit `http://localhost:8000/` and sign in with a user you create via `python manage.py createsuperuser`.

## Running Tests

```bash
pytest
```

## Deploying to Render

1. Push the repository to GitHub.
2. In Render, choose **New +** → **Blueprint** → select this repository containing `render.yaml`.
3. Configure environment variables on the web service: `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` (used by the `ensure_admin` command during deploy).
4. Render provisions PostgreSQL, the Python web service, and the scheduled cron job automatically. The first deploy runs migrations, collects static files with Tailwind CSS, creates the admin account, and serves the app via Gunicorn.
5. Log in with the bootstrap credentials you supplied to start configuring offices, medications, and staff memberships.

## Daily Digest Emails

A scheduled Render cron job runs `python manage.py send_digest_emails --days=60` every day at 08:00 UTC to email summaries of lots approaching expiration. Configure email credentials via environment variables if you need real delivery.

## API Overview

| Endpoint | Description |
| --- | --- |
| `GET /api/offices/` | Offices visible to the authenticated user |
| `GET /api/medications/` | Active medications |
| `GET /api/offices/<id>/stock/` | Office-specific medication catalog |
| `GET /api/offices/<id>/lots/` | Lots for a given office |
| `GET /api/reports/expiring?days=60&office_id=...` | Lots expiring within the selected window |
| `GET /api/reports/expired` | Expired lots |
| `GET /api/reports/inventory` | Aggregate inventory totals |

All API endpoints require session authentication and respect the user’s office memberships.
