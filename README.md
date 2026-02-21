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
4. Start local services (when defined in compose):
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

## Development Commands

Run from repository root unless explicitly noted.

- `make verify`:
  runs formatting/lint hooks, validates required env vars, and checks API + DB
- `make verify-env`:
  validates env vars only (no style checks, API, or DB)
- `make check`:
  runs all pre-commit hooks across the repository
- `npm run check`:
  runs prettier and lint scripts from root `package.json`
- `python scripts/verify.py --skip-api --skip-db`:
  runs style + env checks only
- `python scripts/verify.py --timeout 10`:
  uses a custom timeout for service checks

## Documentation

- `docs/README.md`: documentation entry point
- `apps/frontend/README.md`: frontend scope and responsibilities
- `apps/backend/README.md`: backend scope and responsibilities
