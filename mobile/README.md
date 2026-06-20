<!-- SPDX-License-Identifier: MIT -->

# Carbon Footprint — Mobile (Expo + React Native)

Day-to-day footprint tracking companion. Runs **fully offline out of the box**
(mock API) and shares one API contract with the web app via
`@carbon/shared-types` (the same TypeScript types and zod schemas validate every
`POST /api/footprint` request/response).

## Capabilities

- **App shell + navigation** — a bottom-tab navigator with a **Log** screen
  (form + assisted-capture card) and a **History & insights** screen.
- **Firebase Auth** (email/password) with AsyncStorage-backed RN persistence.
  The ID token is attached as `Authorization: Bearer <token>` and an
  `X-Trace-Id` header is added to every API call.
- **Offline-first log queue** — entries persist locally (AsyncStorage), queue
  when offline, and sync automatically on reconnect (NetInfo). Deduplicated by a
  stable `clientId` (also reused as the request trace id for server-side
  idempotency).
- **API client** mirroring the web (`submitFootprint`) with a mockable mode so
  the app runs without the backend.
- **FCM push-nudge scaffolding** (Expo notifications) — registration + handlers,
  gated to no-op unless `EXPO_PUBLIC_ENABLE_PUSH=true` and an EAS project id are
  set.
- **Opt-in, consented Google Fit + Maps-assisted transport capture** — a consent
  gate (in-app consent + OS permission, both required) that **denies capture by
  default**; nothing location/Fit-derived is read without explicit, revocable
  consent.
- **Accessibility** — `accessibilityLabel`/`accessibilityRole`/
  `accessibilityState` on interactive elements; an exhaustive `switch` over the
  transport-mode union with a `never` default.

## Project structure

```
mobile/
  App.tsx                      # provider stack + bottom-tab navigation
  src/
    config/env.ts              # typed EXPO_PUBLIC_* config (no secrets)
    telemetry/trace.ts         # X-Trace-Id helper
    api/                       # client.ts, errors.ts, mock.ts (mirror web)
    auth/                      # firebase.ts, AuthContext.tsx, useAuth.ts, SignInBar.tsx
    offline/                   # queue.ts, reconnect.ts, store.ts, AsyncStorage/NetInfo adapters, QueueContext
    capture/                   # consent.ts, transport.ts (exhaustive switch), expo-location adapter, ConsentContext
    nudges/push.ts             # gated FCM nudge scaffolding
    screens/                   # LogScreen.tsx, HistoryScreen.tsx
  __tests__/                   # queue.test.ts, consent.test.ts (jest, framework-free)
```

## Configuration

Copy `.env.example` to `.env` and fill in values (none are secrets). With no
backend URL configured the app defaults to the mock API so it runs offline.

## Running & verifying

```bash
npm install
npm run typecheck   # tsc --noEmit
npm test            # jest unit tests (offline-queue sync + consent gate)
npm start           # Expo dev server (device/emulator)
```

> The offline queue, reconnect sync, and consent gate are written as
> dependency-injected, framework-free modules so they are unit-tested in plain
> Node without booting React Native or mocking native modules. For on-device
> runtime, build the shared types once (`npm --prefix ../packages/shared-types
> run build`) so Metro can resolve `@carbon/shared-types` from its `dist`.
