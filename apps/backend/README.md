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

## Feature Extractor Versioning

Feature tables store four metadata fields for reproducibility:

- `extractor_version`
- `window_start`
- `window_end`
- `source_timezone`

Why this exists:

- Feature extraction logic changes over time.
- Keeping `extractor_version` and window metadata allows historical datasets to remain reproducible.

How to bump extractor version:

1. Update `FEATURE_EXTRACTOR_VERSION` in your environment (for example: `v2`).
2. Run feature extraction jobs so new rows are written with the new version.
3. Keep older rows in place to preserve prior training/evaluation datasets.

How to rebuild datasets after extractor changes:

1. Filter feature rows by `extractor_version` for the dataset you want.
2. Recompute model training sets from that fixed version slice.
3. Compare model metrics across versions (`v1` vs `v2`) before promoting.

## Feature Request Endpoint

Create a feature-generation request:

```bash
curl -X POST http://localhost:8000/features/request
```

Expected response:

```json
{
  "requestId": "c6f0e4f1-3d93-4703-9d65-1291d92c8bb2",
  "status": "pending"
}
```

Each request persists a row in `requests` with:

- `status = "pending"`
- `source = "phone"`
