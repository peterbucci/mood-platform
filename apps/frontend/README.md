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

## Run

From repo root:

```bash
npm install
npm run --workspace apps/frontend start
```
