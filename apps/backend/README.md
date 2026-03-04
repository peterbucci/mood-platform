# Backend App

This directory contains the FastAPI backend, repositories, services, and DB migrations.

## Database + Migrations

Canonical command from repo root:

```bash
python -m alembic -c apps/backend/alembic.ini upgrade head
```

From this directory (`apps/backend`), equivalent command:

```bash
alembic -c alembic.ini upgrade head
```

Create a new migration:

```bash
alembic -c alembic.ini revision --autogenerate -m "describe change"
```

The migration environment reads `DATABASE_URL` and converts
`postgresql://...` URLs to `postgresql+psycopg://...` for SQLAlchemy.
