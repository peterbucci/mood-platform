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

## Documentation

- `docs/README.md`: documentation entry point
- `apps/frontend/README.md`: frontend scope and responsibilities
- `apps/backend/README.md`: backend scope and responsibilities
