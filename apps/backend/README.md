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

Request status/cancel endpoints:

- `GET /requests/{id}`
  - returns `{ id, status, featureId, createdAt }`
- `GET /requests/pending/count`
  - returns `{ pendingCount }`
- `DELETE /requests/{id}`
  - if request is `pending`: transitions to `canceled` and returns request payload
  - if request is already `canceled`: returns `200` idempotently
  - if request is `fulfilled`: returns `409` (cancel not allowed)
  - ownership is enforced; unknown/other-user request returns `404`
  - `deleteFeatureToo=true` is reserved and currently returns `409` for fulfilled requests

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

Webhook ingestion endpoint:

- `POST /fitbit/webhook`
  - verifies `X-Fitbit-Signature` against the raw request body with HMAC-SHA256
  - requires `FITBIT_WEBHOOK_SECRET`
  - rejects missing signature with `401`
  - rejects invalid signature with `403`
  - acknowledges quickly with `204` and schedules async debounce processing by user
  - coalesces duplicate events per user within `FITBIT_WEBHOOK_COALESCE_SECONDS`
  - triggers fulfillment once per user after debounce when pending requests exist

Local webhook ingestion test:

1. Set env vars:
   - `FITBIT_WEBHOOK_SECRET`
   - `FITBIT_WEBHOOK_COALESCE_SECONDS` (optional; default `10`)
2. Generate test payload + signature (Python one-liner):
   ```bash
   python - <<'PY'
   import hashlib, hmac
   body = b'[{"ownerId":"fitbit-user-1","collectionType":"sleep","date":"2026-03-05"}]'
   print(hmac.new(b"replace-with-fitbit-webhook-secret", body, hashlib.sha256).hexdigest())
   PY
   ```
3. Send request:
   ```bash
   curl -i -X POST http://localhost:8000/fitbit/webhook \
     -H "Content-Type: application/json" \
     -H "X-Fitbit-Signature: <signature-from-step-2>" \
     -d '[{"ownerId":"fitbit-user-1","collectionType":"sleep","date":"2026-03-05"}]'
   ```

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

## Fitbit Pull Coverage (US-021)

Fulfillment now fetches Fitbit signals per request anchor date (derived from request `created_at`) and
builds one merged feature payload with graceful missing/partial handling.

### Fitbit Fetch Model (Python)

The Python worker now mirrors the Node orchestration model:

- Requests are grouped by `(user, local_day, night_anchor_day, source_timezone)`.
- Day-aligned signals use the request local calendar day.
- Night-aligned signals use a configurable night anchor window.
- `latest_exercise` is fetched per request anchor timestamp (not per date batch).

### Timezone Resolution + Anchoring (US-022)

Feature extraction now resolves timezone per request before any Fitbit/window fetches, then uses
that single resolved timezone for:

- anchor calculation (`local_date`, `night_anchor_date`)
- Fitbit day/range fetch windows (`window_start`, `window_end`)
- context-derived fields like day-of-week/weekend
- persisted feature metadata (`source_timezone`)

Resolution precedence:

1. Fitbit profile timezone (`GET /1/user/-/profile.json`) when available and valid IANA.
2. Client timezone from request `clientFeatures` (`source_timezone`, `timezone`, `tz`, `timeZone`)
   when valid IANA.
3. UTC fallback.

Notes added when Fitbit timezone cannot be used:

- `timezone_from_fitbit_unavailable`
- `timezone_from_fitbit_invalid`
- `timezone_fallback_to_client`
- `timezone_fallback_to_utc`

Timezone fetch call-volume controls:

- Fitbit timezone is cached per user in-process with long TTL.
- `FITBIT_TIMEZONE_CACHE_TTL_SECONDS` (default `604800`, 7 days).
- Missing timezone responses are cached for a shorter window (up to 1 hour) to reduce thrash.
- 403/429/timeout never fail fulfillment; timezone falls back and notes are added.

Night anchor knobs:

- `NIGHT_ANCHOR_START_HOUR` (default `18`)
- `NIGHT_ANCHOR_END_HOUR` (default `12`)
- `FITBIT_DEFAULT_TIMEZONE` (default `UTC`) used when client/request timezone is missing.

Rate-limit/backoff policy:

- Per-user minimum request interval: `FITBIT_MIN_FETCH_INTERVAL_SECONDS` (default `0.2`).
- Bounded parallel Fitbit fetches per user/date batch: `FITBIT_MAX_CONCURRENT_FETCHES` (default `3`).
- Per-signal retry loop: `FITBIT_MAX_RETRIES` (default `2`) with exponential backoff + jitter using `FITBIT_BACKOFF_BASE_SECONDS` (default `0.5`).
- `429` respects `Retry-After` when provided; after retries, the signal is marked missing (`rate_limited`) and fulfillment continues.
- Capability cache for forbidden signals: `FITBIT_FORBIDDEN_CACHE_SECONDS` (default `3600`) reduces repeated 403 thrash per `(user, signal)`.
- Failed requests still persist retry state in `requests` (`attempts`, `nextAttemptAt`, `lastErrorCode`, `lastErrorSignal`) so the worker does not immediately retry the same request in the next loop when a request-level failure occurs.

403 semantics:

- 403 with missing-scope semantics is treated as non-fatal signal-missing (`forbidden_scope`), and token row is marked `needs_reauth=true`.
- `needs_reauth` short-circuits Fitbit pulls to avoid retry thrash until OAuth relink.
- 401 remains auth-fatal for that fetch attempt.

Fitbit endpoints called:

- OAuth authorize: `GET https://www.fitbit.com/oauth2/authorize`
- OAuth token: `POST https://api.fitbit.com/oauth2/token`
- Webhook subscription registration: `POST /1/user/-/activities/apiSubscriptions/1.json`
- Activity summary: `GET /1/user/-/activities/date/{date}.json`
- Intraday steps: `GET /1/user/-/activities/steps/date/{date}/1d/1min.json`
- Intraday calories out: `GET /1/user/-/activities/calories/date/{date}/1d/1min.json`
- Intraday active-zone-minutes: `GET /1/user/-/activities/active-zone-minutes/date/{date}/1d/1min.json`
- Heart daily intraday: `GET /1/user/-/activities/heart/date/{date}/1d/1min.json`
- Heart 7-day: `GET /1/user/-/activities/heart/date/{date}/7d.json`
- Steps 7-day: `GET /1/user/-/activities/steps/date/{date}/7d.json`
- Latest exercise: `GET /1/user/-/activities/list.json?beforeDate={date}&sort=desc&offset=0&limit=1`
- Sleep daily: `GET /1.2/user/-/sleep/date/{date}.json`
- Sleep range: `GET /1.2/user/-/sleep/date/{start}/{end}.json`
- HRV daily: `GET /1/user/-/hrv/date/{date}.json`
- HRV range: `GET /1/user/-/hrv/date/{start}/{end}.json`
- HRV intraday-all: `GET /1/user/-/hrv/date/{date}/all.json`
- Breathing daily: `GET /1/user/-/br/date/{date}.json`
- Breathing range: `GET /1/user/-/br/date/{start}/{end}.json`
- Breathing all: `GET /1/user/-/br/date/{date}/all.json`
- SpO2 daily: `GET /1/user/-/spo2/date/{date}.json`
- SpO2 range: `GET /1/user/-/spo2/date/{start}/{end}.json`
- Skin temp daily: `GET /1/user/-/temp/skin/date/{date}.json`
- Skin temp range: `GET /1/user/-/temp/skin/date/{start}/{end}.json`
- Nutrition summary: `GET /1/user/-/foods/log/date/{date}.json`
- Water logs: `GET /1/user/-/foods/log/water/date/{date}.json`
- User profile (timezone source): `GET /1/user/-/profile.json`

Non-Fitbit context endpoints called (when `clientFeatures.lat/lon` are provided):

- Weather: `GET https://api.open-meteo.com/v1/forecast`
- Air quality: `GET https://air-quality-api.open-meteo.com/v1/air-quality`

Fitbit passthrough endpoint:

- `GET /fitbit/proxy?path=/1/...` or `/1.2/...` forwards to `https://api.fitbit.com{path}`
- `/oauth2/*` is blocked by allowlist/denylist rules

Recommended OAuth scopes for parity:

- `activity`
- `heartrate`
- `sleep`
- `nutrition`
- `oxygen_saturation`
- `respiratory_rate`
- `temperature`
- `profile`

Additional env vars used by this flow:

- `FITBIT_SUBSCRIBER_ID` for subscription registration header `X-Fitbit-Subscriber-Id`
- `WEATHER_CACHE_TTL_SECONDS` for weather/air-quality cache TTL (Redis-backed if `REDIS_URL` exists, else in-memory)
- `FITBIT_MAX_RETRIES` per-signal retries on timeout/429/5xx
- `FITBIT_BACKOFF_BASE_SECONDS` retry backoff base interval
- `FITBIT_MAX_CONCURRENT_FETCHES` bounded signal fetch concurrency
- `FITBIT_FORBIDDEN_CACHE_SECONDS` capability cache TTL for forbidden Fitbit signals
- `FITBIT_TIMEZONE_CACHE_TTL_SECONDS` timezone cache TTL for Fitbit profile timezone resolution

Feature payload notes:

- `missing_hrv`, `partial_hrv`
- `missing_breathing_rate`, `partial_breathing_rate`
- `missing_spo2`, `partial_spo2`
- `missing_temp`, `partial_temp`
- `missing_nutrition`, `partial_nutrition`
- `missing_water`, `partial_water`
- `missing_intraday_steps`
- `missing_intraday_calories`
- `missing_intraday_azm`
- `missing_intraday_heart`
- `missing_weather`
- `missing_air_quality`
- `missing_location_context`
- `timezone_from_fitbit_unavailable`
- `timezone_from_fitbit_invalid`
- `timezone_fallback_to_client`
- `timezone_fallback_to_utc`

Behavior rules:

- Missing/partial signal data never fails full fulfillment.
- Derived fields for missing signals are emitted as `null`.
- `401` is treated as auth failure for the pull and retries via token refresh.
- `403`/`404`/`5xx`/malformed JSON become per-signal missing markers.
- `429` is retried per signal and then converted to per-signal missing markers when retries are exhausted.

Feature module layout:

- Feature math is split under `app/services/features/` (composites, context enrichment, field registry, heart helpers).
- `fitbit_feature_builder.py` remains the orchestrator that composes module outputs into the stable payload contract.

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

### Manual Flow (OAuth -> Request -> Webhook -> Fulfillment)

1. Connect Fitbit OAuth (`GET /fitbit/oauth/start` -> callback).
2. Create pending request (`POST /features/request`).
3. Send Fitbit webhook payload to `POST /fitbit/webhook` (valid signature).
4. Ensure worker is running (`python -m app.worker` or docker compose worker).
5. Read `GET /features/latest` and verify data now includes:
   - `activity`, `hrv`, `breathing_rate`, `spo2`, `temp`, `nutrition`, `water`, `notes`.

### Local Verification (403/429 behavior)

1. Start worker:
   - `PYTHONPATH=apps/backend python -m app.worker`
2. Trigger a request:
   - `curl -X POST http://localhost:8000/features/request`
3. Simulate mocked 429/403 in tests:
   - `python -m pytest apps/backend/tests/test_fitbit_api_client.py apps/backend/tests/test_fitbit_data_client.py apps/backend/tests/test_request_backoff_scheduling.py -q`
4. Confirm retry scheduling:
   - `SELECT id, attempts, "nextAttemptAt", "lastErrorCode", "lastErrorSignal" FROM requests WHERE status='pending';`
5. Confirm forbidden breathing still fulfills with note:
   - `python -m pytest apps/backend/tests/test_request_fulfillment_static_payload.py -q`

### Local Verification (US-022 timezone precedence/caching)

Run:

- `python -m pytest apps/backend/tests/test_fitbit_anchoring.py -q`
- `python -m pytest apps/backend/tests/test_fitbit_api_client.py -q`
- `python -m pytest apps/backend/tests/test_fitbit_data_client.py -q`
- `python -m pytest apps/backend/tests/test_request_fulfillment_static_payload.py -q`

Expected:

- Fitbit profile timezone overrides client timezone when valid.
- Failed Fitbit profile timezone fetches fall back to client timezone (if valid) else UTC.
- Fallback notes are present in feature payload `notes`.
- Repeated timezone fetches for the same user reuse cache instead of re-calling Fitbit immediately.
