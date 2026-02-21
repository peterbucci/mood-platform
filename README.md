# mood-platform

Single-owner, self-hostable mood platform monorepo.

## Repository Structure

```text
mood-platform/
├─ apps/
│  ├─ frontend/      # Expo frontend app (scaffold)
│  └─ backend/       # FastAPI backend app (scaffold)
├─ docs/             # architecture and developer docs
├─ scripts/          # repository utility scripts
├─ .env.example
├─ Makefile
├─ MONOREPO.md
└─ README.md
```

## Quick Start

1. Clone the repository.
2. Copy environment variables:
   - `cp .env.example .env` (macOS/Linux)
   - `Copy-Item .env.example .env` (PowerShell)
3. Start local services (when defined in compose):
   - `docker compose up -d`
4. Run repository verification:
   - `make verify`
   - fallback: `python scripts/verify.py`

## Development Commands

Run from repository root unless explicitly noted.

- `make verify`:
  validates required env vars, API health endpoint, and DB connectivity
- `python scripts/verify.py --skip-api --skip-db`:
  validates environment only
- `python scripts/verify.py --timeout 10`:
  uses a custom timeout for service checks

## Command Scope

- Root-level commands:
  repository-wide tooling, verification, and standards checks
- App-level commands:
  app-specific run/test commands (from `apps/frontend` or `apps/backend` once app code is added)

## Tooling and Code Style

- `.editorconfig` defines base editor behavior for all files.
- Formatting/linting standards are defined at the repository root so both apps follow the same rules.
- Pre-commit hooks will enforce formatting and lint checks on each commit.

## Documentation

- `MONOREPO.md`: high-level repository scaffold
- `docs/README.md`: documentation entry point
- `apps/frontend/README.md`: frontend scope and responsibilities
- `apps/backend/README.md`: backend scope and responsibilities
