# Frontend Notes

This directory covers the Expo React Native frontend for Mood Platform.

## App Shell

Implemented foundation:

- Expo app setup
- React Navigation stack routing
- Shared app layout with header, navigation, and page container
- Core pages for:
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

## Fitbit Connection Status And Settings

Implemented:

- `Settings` screen loads Fitbit OAuth connection status from the backend
- UI states for:
  - loading
  - disconnected
  - connected
  - error
- Connect action opens Fitbit OAuth start flow
- Disconnect action calls the backend unlink endpoint
- Refresh action re-checks status
- Reusable `FitbitConnectionCard` component for connected and disconnected states
- Backend-managed Fitbit integration configuration form with masked secret fields

Backend endpoints used:

- `GET /fitbit/oauth/status`
- `GET /fitbit/oauth/start`
- `POST /fitbit/oauth/unlink`
- `GET /settings/fitbit`
- `PUT /settings/fitbit`

## Frontend API Client And Environment Config

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

## Environment Variable

Set:

```bash
EXPO_PUBLIC_API_BASE_URL=http://<backend-host>:8000
```

Examples:

- Android emulator to local machine: `http://10.0.2.2:8000`
- iOS simulator to local machine: `http://localhost:8000`
- Physical device on the same LAN: `http://<your-lan-ip>:8000`
- Tunnel: `https://<subdomain>.ngrok.app`

Important:

- `localhost` usually does not work on a physical device.
- The API base URL must be a full absolute URL including protocol.
- Frontend startup fails clearly if `EXPO_PUBLIC_API_BASE_URL` is missing or invalid.

## Run

From the repo root:

```bash
npm install
npm run --workspace apps/frontend start
```

If using a physical device, make sure `EXPO_PUBLIC_API_BASE_URL` points to a host the device can reach.
