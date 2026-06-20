<!-- SPDX-License-Identifier: MIT -->

# Carbon Footprint — Mobile (Expo + React Native)

> **Status: ROADMAP STUB (plan Phase 9).** This is an intentional scaffold, not
> a finished app. It exists to prove the mobile target compiles against the
> shared contract and to anchor the post-MVP build.

## What this stub demonstrates

- **Shared contract reuse.** The app imports `@carbon/shared-types`
  (`file:../packages/shared-types`) — the *same* TypeScript types and zod
  schemas the web app uses for `POST /api/footprint`. There is one source of
  truth for request/response shapes and validation across web and mobile.
- A single placeholder screen listing the transport modes (sourced from
  shared-types) and the planned capabilities below.

## Planned capabilities (built post-MVP)

- **Offline-first logging.** A local log queue persists footprint entries while
  offline and syncs to the backend on reconnect (idempotent, dedup on client
  event id). Day-to-day tracking should never require connectivity.
- **FCM nudges.** Firebase Cloud Messaging delivers streak reminders and
  weekly-challenge nudges; batched server-side to control cost.
- **Firebase Auth.** Same ID-token contract as web: obtain the Firebase ID
  token and attach it as `Authorization: Bearer <token>` on API calls.
- **Opt-in Google Fit + Maps transport capture.** Strictly consented; assisted
  trip-distance/mode detection. **No location or fitness data is captured
  without explicit, revocable user permission**, and never in the background
  without consent.

## Accessibility (roadmap gate)

Screen-reader labels (`accessibilityLabel`/`accessibilityRole`) on every
interactive element, adequate touch-target sizes, and sufficient contrast — to
be verified before this target ships.

## Running the stub (once dependencies are installed)

```bash
npm install     # installs Expo + shared-types (file: dependency)
npm run typecheck
npm start        # launches the Expo dev server
```

> The full app is **not** built in this slice. Phase 9 owns the implementation;
> Phase 5 owns end-to-end verification.
