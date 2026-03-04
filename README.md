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

Run backend migrations in the Docker environment:

```bash
docker compose run --rm api alembic -c alembic.ini upgrade head
```

Create a new migration after model changes:

```bash
docker compose run --rm api alembic -c alembic.ini revision --autogenerate -m "describe change"
```

Reset database state (drop all Postgres data) and re-run migrations:

```bash
docker compose down -v
docker compose up -d postgres
docker compose run --rm api alembic -c alembic.ini upgrade head
```

Quick verification flow for mood entry + FK links:

```bash
docker compose up --build -d
docker compose run --rm api alembic -c alembic.ini upgrade head
```

```bash
# Create a feature row and capture IDs
docker compose exec postgres psql -U mood -d mood -c "INSERT INTO users (id) VALUES ('00000000-0000-0000-0000-000000000001') ON CONFLICT DO NOTHING;"
docker compose exec postgres psql -U mood -d mood -c "INSERT INTO sleep_features (id, user_id, captured_at) VALUES ('11111111-1111-1111-1111-111111111111', '00000000-0000-0000-0000-000000000001', now());"
```

```bash
curl -X POST http://localhost:8000/moods \
  -H "Content-Type: application/json" \
  -d '{
    "entry_at": "2026-03-04T12:00:00Z",
    "label_category_key": "calm",
    "label_emotion": "Relaxed",
    "note": "steady afternoon",
    "feature_set_ids": {
      "sleep_features_id": "11111111-1111-1111-1111-111111111111"
    }
  }'
```

```bash
docker compose exec postgres psql -U mood -d mood -c "SELECT m.id, m.sleep_features_id, s.id AS linked_sleep_id FROM mood_entries m JOIN sleep_features s ON s.id = m.sleep_features_id ORDER BY m.created_at DESC LIMIT 1;"
```

## Documentation

- `docs/README.md`: documentation entry point
- `apps/frontend/README.md`: frontend scope and responsibilities
- `apps/backend/README.md`: backend scope and responsibilities
