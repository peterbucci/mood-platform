# Getting Started

This guide covers the shared local-development setup for the Mood Platform monorepo.

## Prerequisites

- Docker Desktop
- Python
- Node.js and npm

## First-Time Setup

1. Copy the environment template.
   - PowerShell: `Copy-Item .env.example .env`
   - macOS/Linux: `cp .env.example .env`
2. Install repository tooling.
   - `pip install pre-commit`
   - `npm install`
   - `pre-commit install`
3. Start local services.
   - `docker compose up -d`
4. Verify the repo.
   - `make verify`
   - fallback: `python scripts/verify.py`

## Local Development Stack

Run the full stack:

```bash
docker compose up --build
```

Check readiness:

```bash
curl http://localhost:8000/health/ready
```

Stop services:

```bash
docker compose down
```

Reset services and volumes:

```bash
docker compose down -v
```

## Database And Migrations

Canonical migration command from the repo root:

```bash
python -m alembic -c apps/backend/alembic.ini upgrade head
```

Set `DATABASE_URL` before running migrations.

PowerShell example:

```powershell
$env:DATABASE_URL="postgresql://mood:mood@localhost:5432/mood"
python -m alembic -c apps/backend/alembic.ini upgrade head
```

Optional `Makefile` shortcuts:

```bash
make db-up
make migrate
make migrate-sql
make revision MSG="describe change"
make db-down
```

Create a new migration after model changes:

```bash
python -m alembic -c apps/backend/alembic.ini revision --autogenerate -m "describe change"
```

If a migration fails:

1. Confirm PostgreSQL is running: `docker compose up -d postgres`
2. Verify `DATABASE_URL` points to the running database.
3. Retry the migration command.

Reset the local DB and reapply migrations:

```bash
docker compose down -v
docker compose up -d postgres
python -m alembic -c apps/backend/alembic.ini upgrade head
```

## Environment Notes

Required for normal local runtime:

- `DATABASE_URL`
- `EXPO_PUBLIC_API_BASE_URL`
- `APP_SECRET_ENCRYPTION_KEY` for encrypted integration-secret storage

Fitbit configuration is now managed through the app itself:

- Save OAuth credentials and webhook secrets from `Settings -> Fitbit Integration`
- Old Fitbit credential env vars are no longer required for normal runtime operation
- `FITBIT_WEBHOOK_COALESCE_SECONDS` remains environment-driven

## More Documentation

- [Frontend Notes](frontend/README.md)
- [Backend Notes](backend/README.md)
