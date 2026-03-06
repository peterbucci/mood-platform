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

## Run

From repo root:

```bash
npm install
npm run --workspace apps/frontend start
```
