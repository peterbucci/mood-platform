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

1. Copy `.env.example` to `.env` once available.
2. Start services with `docker compose up`.
3. Run verification with `make verify` (or project equivalent) when added.

## Repository Baseline Files

- `README.md`
- `LICENSE`
- `.gitignore`
- `.editorconfig`
