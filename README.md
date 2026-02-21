# mood-platform

Baseline repository for the rebuilt mood platform.

## Overview

This project is a single-owner, self-hostable system for:

- capturing mood entries
- enriching them with Fitbit-derived features
- storing versioned, ML-ready data

## Planned Stack

- FastAPI (backend API)
- PostgreSQL (primary database)
- Redis (queue/cache)
- Expo (mobile client)
- Docker Compose (local orchestration)

## Quick Start (Baseline)

1. Copy `.env.example` to `.env`.
2. Start services with `docker compose up`.
3. Run verification with `make verify`.

## Verification

Run:

```bash
make verify
```

If `make` is not available on your machine, run:

```bash
python scripts/verify.py
```

The verification script will:

- validate required environment variables and clearly list any missing ones
- call the configured API health endpoint
- verify database connectivity by executing `SELECT 1`

## Repository Baseline Files

- `README.md`
- `LICENSE`
- `.gitignore`
- `.editorconfig`
