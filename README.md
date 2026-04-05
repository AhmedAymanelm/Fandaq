# RAHATY Hotels Group Platform

نظام إدارة وتشغيل فنادق متعدد الفروع يجمع بين إدارة العمليات اليومية، المتابعة المالية، وخدمات الضيوف عبر القنوات الرقمية في منصة واحدة.

هذا المشروع مبني كنظام SaaS متعدد المستأجرين (Multi-Tenant) لتمكين كل فندق من إدارة بياناته وعملياته بشكل مستقل، مع لوحة تحكم مركزية للإدارة والفرق التشغيلية.

## Project Overview

RAHATY is a production-focused hospitality platform designed for:

- Hotel operations and reservations lifecycle management
- Staff workflow management with role-based access control
- Daily pricing intelligence and competitor comparison
- Performance analytics for staff supervision
- Email-based operational reporting with Excel exports

The platform is optimized for real-world usage where reliability, traceability, and clear reporting are required for day-to-day hotel execution.

## Core Capabilities

- Multi-hotel architecture with per-hotel data isolation
- Reservation flow: pending, approval, check-in, check-out, cancellation, rejection
- Complaint and service-request workflow with ownership tracking
- Daily pricing module with competitor benchmarking and report exports
- Unified reporting delivery (pricing + staff performance) via email
- Role model for admin, supervisor, and employee with scoped permissions
- Dashboard modules for rooms, guests, reviews, expenses, reports, and users

## Technology Stack

- Backend: FastAPI, SQLAlchemy Async, Alembic
- Database: PostgreSQL
- Frontend: HTML, CSS, Vanilla JavaScript (single dashboard application)
- Scheduling: APScheduler
- Reporting: OpenPyXL (Excel generation)
- Email delivery: aiosmtplib

## High-Level Structure

```text
app/
   api/           HTTP endpoints and dependencies
   models/        SQLAlchemy entities
   schemas/       Pydantic contracts
   services/      Business logic and background jobs
   main.py        FastAPI entrypoint

alembic/
   versions/      Database migration history

dashboard/
   index.html     Main dashboard shell
   css/           Styling
   js/            Frontend views and API client

tests/
   test_smoke_release.py   Release smoke checks
```

## Local Setup

1. Create and activate virtual environment.
2. Install dependencies.
3. Configure environment variables.
4. Apply migrations.
5. Run the application.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
venv/bin/alembic upgrade head
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
```

Dashboard URL:

```text
http://localhost:8000/dashboard/
```

## Environment Notes

Minimum required configuration for normal runtime:

- DATABASE_URL
- SECRET_KEY
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

Optional integrations:

- OPENAI_API_KEY
- WHATSAPP_API_TOKEN and related WhatsApp settings
- TELEGRAM_BOT_TOKEN and related Telegram settings

## Release Smoke Tests

The repository includes smoke tests to validate critical release paths:

- Migration head vs current database revision
- Authentication login path
- Report send endpoint behavior

Run smoke tests:

```bash
venv/bin/python -m pytest -q tests/test_smoke_release.py
```

## Database and Migration Discipline

- Any schema update must be accompanied by a new Alembic migration.
- Deployment should always run `venv/bin/alembic upgrade head` before application startup.
- Automated combined reports are sent daily at 12:00 AM (midnight), covering the previous day.
- Current project revision chain includes operational migrations for pricing, actor tracking, and user email support.

## License

Private project. All rights reserved.
