# Backend Notes

This directory contains the FastAPI backend, repositories, services, DB migrations,
and the fulfillment worker runtime.

## Database + Migrations

Canonical command from repo root:

```bash
python -m alembic -c apps/backend/alembic.ini upgrade head
```

From `apps/backend`, the equivalent command is:

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

1. Update `FEATURE_EXTRACTOR_VERSION` in your environment.
2. Run feature extraction jobs so new rows are written with the new version.
3. Keep older rows in place to preserve prior training and evaluation datasets.

How to rebuild datasets after extractor changes:

1. Filter feature rows by `extractor_version` for the dataset you want.
2. Recompute model training sets from that fixed version slice.
3. Compare model metrics across versions before promoting.

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

## Seed Demo Data

Populate synthetic request, feature, and label history over the last 30 days:

```bash
python apps/backend/scripts/seed_recent_requests_features_labels.py --count 100 --days 30
```

Useful options:

- `--user-id <uuid>` override owner user id
- `--append` keep existing seeded rows and add more
- `--source <text>` custom source tag
- `--fulfilled-ratio 0.75` controls status mix

Notes:

- Requires `DATABASE_URL` to be set.
- By default, previously seeded rows for the same user and source are replaced.

Feature read/delete endpoints:

- `GET /features/latest`
- `GET /features/{id}`
- `GET /features`
- `DELETE /features/{id}`
  - deletes the feature for the current user
  - deletes every request linked to that feature
  - deletes linked `labels`
  - runs as one transaction, so no partial cleanup is committed

Request status/delete endpoints:

- `GET /requests/{id}`
- `GET /requests/pending/count`
- `DELETE /requests/{id}`
  - deletes the request for the current user
  - if the request is linked to a feature snapshot, deletes that snapshot too
  - deletes linked `labels`
  - if legacy data has multiple requests linked to the same snapshot, deleting either side deletes the full connected unit
  - ownership is enforced; unknown or other-user request returns `404`
  - runs as one transaction, so cleanup is fully committed or fully rolled back

## Fitbit OAuth

The backend supports Fitbit OAuth connect and disconnect endpoints:

- `GET /fitbit/oauth/start`
- `GET /fitbit/oauth/callback`
- `GET /fitbit/oauth/status`
- `POST /fitbit/oauth/unlink`

Fitbit integration settings endpoints:

- `GET /settings/fitbit`
  - returns the saved Fitbit configuration for the single-owner app
  - masks stored secrets
- `PUT /settings/fitbit`
  - creates or updates the singleton `integration_settings` row
  - validates `clientId`, `clientSecret`, and `redirectUri`
  - preserves the existing client secret when the update omits it
  - encrypts secret values before writing them to the database

Configuration loading flow:

1. The owner saves Fitbit OAuth credentials in the frontend Settings screen.
2. The backend encrypts `clientSecret` and `webhookSecret` with `APP_SECRET_ENCRYPTION_KEY`.
3. Ciphertext is stored in the `integration_settings` table; plaintext is discarded.
4. FastAPI Fitbit dependencies decrypt those values only when building runtime Fitbit settings.
5. OAuth start/callback, token refresh, webhook verification, and worker Fitbit pulls all read the same stored configuration.
6. If no saved configuration exists, Fitbit OAuth and webhook flows return `Fitbit integration not configured.`

Required secret-management environment variable:

- `APP_SECRET_ENCRYPTION_KEY`

Managed in the database through `PUT /settings/fitbit`:

- Fitbit client id
- Fitbit client secret
- Fitbit redirect URI
- Fitbit OAuth scope
- Fitbit subscriber id
- Fitbit webhook secret

Still environment-driven:

- `APP_SECRET_ENCRYPTION_KEY`
- `FITBIT_AUTH_BASE_URL`
- `FITBIT_TOKEN_URL`
- `FITBIT_WEBHOOK_COALESCE_SECONDS`

## Fulfillment Worker

The worker continuously polls pending feature requests and attempts fulfillment.
It runs independently from the API process.

Run locally from `apps/backend`:

```bash
python -m app.worker
```

From the repo root, set `PYTHONPATH`:

```bash
PYTHONPATH=apps/backend python -m app.worker
```

The worker requires:

- `DATABASE_URL`
- optional `FITBIT_STATIC_PAYLOAD`

Useful worker env vars:

- `WORKER_BASE_IDLE_SLEEP_SECONDS`
- `WORKER_MAX_IDLE_SLEEP_SECONDS`
- `WORKER_BACKOFF_MULTIPLIER`
- `WORKER_USER_BATCH_SIZE`
- `WORKER_REQUEST_BATCH_SIZE`
- `WORKER_LOCK_TTL_SECONDS`
- `WORKER_OWNER_ID`
- `WORKER_HEALTH_PORT`

Health endpoint:

```bash
curl http://localhost:3001/healthz
```

### Docker Compose Worker

Start worker with the local stack:

```bash
docker compose up --build
```

Or worker only:

```bash
docker compose up --build worker
```

### Troubleshooting

- If requests remain `pending`, verify migrations are at head.
- If multiple workers run, per-user TTL locks in `worker_locks` prevent concurrent processing.
- If the healthcheck fails, verify worker logs and `WORKER_HEALTH_PORT`.
