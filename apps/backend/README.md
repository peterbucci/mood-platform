# Backend App

This directory contains the FastAPI backend, repositories, services, DB migrations,
and the fulfillment worker runtime.

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

## Fitbit OAuth

The backend supports Fitbit OAuth connect/disconnect endpoints:

- `GET /fitbit/oauth/start`
- `GET /fitbit/oauth/callback`
- `GET /fitbit/oauth/status`
- `POST /fitbit/oauth/unlink`

Webhook verification endpoint:

- `GET /fitbit/webhook?verify=<challenge>`
  - returns HTTP 200 with plain-text body equal to `<challenge>`
  - returns HTTP 400 with `Missing verification challenge` when `verify` is missing

Required environment variables:

- `FITBIT_CLIENT_ID`
- `FITBIT_CLIENT_SECRET`
- `FITBIT_REDIRECT_URI`

Optional:

- `FITBIT_AUTH_BASE_URL` (default: `https://www.fitbit.com/oauth2/authorize`)
- `FITBIT_TOKEN_URL` (default: `https://api.fitbit.com/oauth2/token`)
- `FITBIT_OAUTH_SCOPE` (default: `sleep heartrate activity profile`)

Local verification:

1. Set Fitbit OAuth env vars.
2. Start API (`docker compose up --build api` or full stack).
3. Open docs at `http://localhost:8000/docs`.
4. Call `/fitbit/oauth/start` and confirm redirect URL includes state and scopes.
5. Complete callback flow (or run tests with mocked token exchange).

Token persistence:

- OAuth states and token records are persisted in:
  - `fitbit_oauth_states`
  - `fitbit_tokens`
- Unlink removes the stored connection row for the owner user.

## Fitbit Token Lifecycle

Tokens are persisted durably in `fitbit_tokens` with:

- `access_token`
- `refresh_token`
- `expires_at`
- `scope`
- optional `fitbit_user_id`

Runtime token usage contract:

1. Fitbit API callers should retrieve tokens through `FitbitTokenService.get_access_token(...)`.
2. `get_access_token` refreshes proactively when token expiry is near (60s skew).
3. `FitbitApiClient.fitbit_fetch(...)` retries once on `401` after refreshing tokens.
4. Missing token state raises a typed not-connected error (`FitbitTokenNotConnectedError`).

Required OAuth refresh env vars:

- `FITBIT_CLIENT_ID`
- `FITBIT_CLIENT_SECRET`

## Fulfillment Worker

The worker continuously polls pending feature requests and attempts fulfillment.
It runs independently from the API process.

Run locally from `apps/backend`:

```bash
python -m app.worker
```

From repo root, set `PYTHONPATH`:

```bash
PYTHONPATH=apps/backend python -m app.worker
```

The worker requires:

- `DATABASE_URL`
- optional `FITBIT_STATIC_PAYLOAD` (JSON object used as feature payload fallback)

Useful worker env vars:

- `WORKER_BASE_IDLE_SLEEP_SECONDS` (default `1`)
- `WORKER_MAX_IDLE_SLEEP_SECONDS` (default `5`)
- `WORKER_BACKOFF_MULTIPLIER` (default `2`)
- `WORKER_USER_BATCH_SIZE` (default `100`)
- `WORKER_REQUEST_BATCH_SIZE` (default `100`)
- `WORKER_LOCK_TTL_SECONDS` (default `30`)
- `WORKER_OWNER_ID` (optional explicit worker identity)
- `WORKER_HEALTH_PORT` (default `3001`)

Health endpoint:

```bash
curl http://localhost:3001/healthz
```

Example response:

```json
{
  "status": "ok",
  "shutting_down": false,
  "in_flight": false,
  "last_loop_at": "2026-03-04T22:15:19.123456+00:00"
}
```

Graceful shutdown:

- On `SIGTERM`/`SIGINT`, the worker stops taking new work.
- It finishes the in-flight iteration and exits cleanly.

### Docker Compose Worker

Start worker with the local stack:

```bash
docker compose up --build
```

Or worker only:

```bash
docker compose up --build worker
```

The `worker` service has a Docker healthcheck that probes:

- `GET http://127.0.0.1:3001/healthz`

### Troubleshooting

- If requests remain `pending`, verify migrations are at head (worker locks table included):
  - `python -m alembic -c apps/backend/alembic.ini upgrade head`
- If multiple workers run, per-user TTL locks in `worker_locks` prevent concurrent processing.
- If healthcheck fails, verify worker logs and `WORKER_HEALTH_PORT`.
