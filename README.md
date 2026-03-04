# mood-platform

Single-owner, self-hostable mood platform monorepo.

## Repository Structure

```text
mood-platform/
|- apps/
|  |- frontend/      # Expo frontend app (scaffold)
|  `- backend/       # FastAPI backend app (scaffold)
|- docs/             # architecture and developer docs
|- scripts/          # repository utility scripts
|- .env.example
|- Makefile
`- README.md
```

## Quick Start

1. Clone the repository.
2. Copy environment variables:
   - `cp .env.example .env` (macOS/Linux)
   - `Copy-Item .env.example .env` (PowerShell)
3. Install developer tooling:
   - `pip install pre-commit`
   - `npm install`
   - `pre-commit install`
4. Start local services:
   - `docker compose up -d`
5. Run repository verification:
   - `make verify`
   - fallback: `python scripts/verify.py`

## Local Development (Docker)

Run the local stack (Postgres, Redis, API):

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

## Database + Migrations

Canonical migration command (run from repo root):

```bash
python -m alembic -c apps/backend/alembic.ini upgrade head
```

Set `DATABASE_URL` before running migrations.

PowerShell example:

```powershell
$env:DATABASE_URL="postgresql://mood:mood@localhost:5432/mood"
python -m alembic -c apps/backend/alembic.ini upgrade head
```

Optional shortcuts via `Makefile`:

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

1. Confirm PostgreSQL is running: `docker compose up -d postgres` (or `make db-up`)
2. Verify `DATABASE_URL` points to the running database.
3. Retry migration: `python -m alembic -c apps/backend/alembic.ini upgrade head`

Reset local DB (drop volume data) and reapply migrations:

```bash
docker compose down -v
docker compose up -d postgres
python -m alembic -c apps/backend/alembic.ini upgrade head
```

## Documentation

- `docs/README.md`: documentation entry point
- `apps/frontend/README.md`: frontend scope and responsibilities
- `apps/backend/README.md`: backend scope and responsibilities
