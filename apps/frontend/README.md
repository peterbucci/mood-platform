# Frontend App

This directory contains the Expo React Native frontend for Mood Platform.

## FE-01 App Shell

Implemented foundation:

- Expo app setup
- React Navigation stack routing
- Shared app layout (header, navigation, page container)
- Placeholder pages for:
  - `/dashboard`
  - `/requests`
  - `/features`
  - `/features/:id`
  - `/settings`
  - fallback `NotFound` route
- Shared UI state components:
  - `LoadingState`
  - `EmptyState`
  - `ErrorState`

## FE-02 Fitbit Connection Status (Settings)

Implemented:

- `Settings` screen now loads Fitbit OAuth connection status from backend
- Supported UI states:
  - loading
  - disconnected
  - connected
  - error
- Connect action opens Fitbit OAuth start flow
- Disconnect action calls backend unlink endpoint
- Refresh action re-checks status
- Reusable `FitbitConnectionCard` component for connected/disconnected states
- Frontend tests for status rendering and connect/disconnect actions

Backend endpoints used:

- `GET /fitbit/oauth/status`
- `GET /fitbit/oauth/start`
- `POST /fitbit/oauth/unlink`

Set API base URL (recommended for device testing):

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

## FE-10 Frontend API Client + Environment Config

Implemented:

- Centralized environment config in `src/config/env.ts`
- Centralized API client in `src/api/client.ts` with:
  - base URL prefixing
  - `apiGet`, `apiPost`, `apiDelete`, `apiPatch`
  - shared JSON handling
  - normalized API errors
- Shared error helpers in `src/api/errors.ts`
- Typed endpoint modules:
  - `src/api/fitbit.ts`
  - `src/api/requests.ts`
  - `src/api/features.ts`

### Environment variable

Set:

```bash
EXPO_PUBLIC_API_BASE_URL=http://<backend-host>:8000
```

Examples:

- Android emulator to local machine: `http://10.0.2.2:8000`
- iOS simulator to local machine: `http://localhost:8000`
- Physical device on same LAN: `http://<your-lan-ip>:8000`
- Tunnel (ngrok): `https://<subdomain>.ngrok.app`

Important:

- `localhost` usually does not work on a physical device.
- The API base URL must be a full absolute URL including protocol (`http://` or `https://`).
- Frontend startup fails clearly if `EXPO_PUBLIC_API_BASE_URL` is missing/invalid.

### Expo startup

From repo root:

```bash
npm install
npm run --workspace apps/frontend start
```

If using a physical device, ensure `EXPO_PUBLIC_API_BASE_URL` points to a LAN IP or tunnel URL that the device can reach.

## Run

From repo root:

```bash
npm install
npm run --workspace apps/frontend start
```
