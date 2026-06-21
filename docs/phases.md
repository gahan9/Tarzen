<!-- SPDX-License-Identifier: MIT -->

# Phased roadmap

Delivery is split into reviewable phases under the PR budget
(`.ai/rules/pr-budget.md`). Phases 0-5 are the shipped MVP + submission package;
Phases 6-9 are designed now with ports/stubs in place and built post-MVP.

| Phase | Scope | Done-gate | Status |
|-------|-------|-----------|--------|
| **0** | Monorepo dirs, `backend/pyproject.toml`, CI repoint + DCO/commitlint, `.env.example`, typed `BaseSettings` (`SecretStr`), SPDX headers, README | `uv sync` works; ruff/mypy clean; CI green; config rejects missing env (2 tests) | ✅ Done |
| **1** | Pydantic schemas + typed error envelope + field bounds; `emission_factors.json`; rule-based `transport.py` (cached factors); `POST /api/footprint` + exception handler; committed OpenAPI | Golden-table kg CO₂e correct; coverage ≥ 80% | ✅ Done |
| **2** | Benchmark catalogue + cross-reference; Vertex AI Gemini gateway (timeout/semaphore/retry/token cap); structured-output schema; Plan/Execute/Evaluate; ask-for-context; phrasing-only LLM; fallback | Mocked-Gemini tests incl. prompt-injection + missing-data; rule-based result unchanged when LLM off | ✅ Done |
| **3** | Vite React+TS shell + Firebase Auth (ID token on calls); footprint form + insight card with loading/empty/error states; a11y | axe/Lighthouse-CI ≥ target (0.95); keyboard nav; error/empty states render | ✅ Done |
| **4** | Dockerfile, `cloudbuild.yaml`, `/healthz` + `/readyz`, structured JSON logging (no PII); data-minimized Firestore write; aggregate-only BigQuery; least-privilege SA roles | Container builds; `/readyz` green with mocked clients; no PII | ✅ Done |
| **5** | Full gate suite green; `architecture.md`, `evaluation-mapping.md`, `threat-model.md`, `data-sources.md`, `data-governance.md`, `ai-tool-usage.md`, `phases.md`; `THIRD_PARTY_NOTICES.md`; license audit; domain skill + adapters | Full gate suite green; license audit clean; evidence pack links every criterion to proof | ✅ Done |
| **6** | Multi-domain trackers (energy/food/shopping/waste) behind `DomainTracker` port; versioned factors; quick-log + recurring; per-domain reduction plans | Golden-table tests per tracker; new domain adds with **zero core edits** | ⏳ Roadmap (ports + stubs in `domain/trackers/*`) |
| **7** | Event-driven gamification: Pub/Sub footprint events → Cloud Function aggregation → Firestore streaks/points + partitioned BigQuery; badges/tiers; server-side anti-cheat | Idempotent replayable consumer; deterministic scoring tests | 🟡 Largely delivered — live scoring runs **synchronously in the request path** (gated by the processed-event ledger for idempotency) with server-side anti-cheat and a verified-ticket bonus; Pub/Sub publish retained for analytics. The async Cloud Function consumer (`functions/aggregate_consumer.py`) remains a stub. |
| **8** | Competitive leaderboard: Memorystore ZSET ranks (friends/teams/global); weekly-challenge reset via Cloud Scheduler; percentile display; Firestore durable snapshot | O(log n) update; stable tie-break; snapshot/restore tested | 🟡 Largely delivered — anonymous **region/global leaderboard** with percentile + rule-based tips is live (`GET /api/leaderboard`); the `LeaderboardStore` port ships both in-memory and Memorystore ZSET backends, selected by `REDIS_HOST` (Terraform provisions the instance). Weekly-challenge reset via Cloud Scheduler is still roadmap. |
| **9** | React Native + Expo mobile: shared-types reuse; offline-first log queue + sync; Firebase Auth; FCM nudges; opt-in Google Fit + Maps transport capture | Offline sync on reconnect; a11y labels; no location without consent | ⏳ Roadmap (`mobile/` Expo stub, `packages/shared-types`) |

## Carbon savings, verified tickets, and regional leaderboard (delivered)

A vertical slice spanning parts of Phases 7-8 shipped on top of the MVP, adding
*avoided-emissions* tracking and an anonymous competitive leaderboard:

- **Savings domain** (`domain/savings.py`): `saved = baseline_solo_car - actual`,
  clamped at ≥ 0, reusing the existing DEFRA factors — no new factor source.
  Carpool: `car_factor × distance × (1 − 1/passengers)`; transit:
  `(car_factor − transit_factor) × distance`. Golden-table tested.
- **Endpoints**: `POST /api/savings` (manual/carpool), `POST /api/savings/import`
  (CSV trip history), `POST /api/savings/ticket` (image → Gemini vision → Maps
  Distance Matrix → server-verified saving + bonus), `GET /api/leaderboard`
  (region/global, percentile, tips), `GET /api/profile` (anon handle + state).
  All five are documented in `docs/openapi.json`.
- **Anonymity + privacy**: a `profiles` collection maps `uid →
  {anon_handle, region}`; region comes from a load-balancer geo header behind a
  `RegionResolver` port (no bundled GeoIP DB). Only the anon handle + score are
  ever returned. See `docs/threat-model.md` §6-8.
- **Anti-cheat**: points are server-authoritative; the verification bonus is
  granted only for server-verified tickets, never from client input.
- **Image-abuse controls**: content-type/size caps, image-hash dedupe to block
  re-submitting the same ticket, and no image bytes logged or persisted.
- **Frontend**: routed SPA (`/`, `/savings`, `/leaderboard`, `/profile`) with an
  emoji-anchored, a11y-labelled UI and a procedurally generated, lazy-loaded
  `@react-three/fiber` savings visualization (zero binary assets; `three` lands
  in a separate async chunk — see `docs/architecture.md` / PR notes for sizes).

## Roadmap design notes

- **Zero-core-edit domains**: new trackers register in
  `domain/registry.py:build_default_registry` via the `DomainTracker` port; the
  API and application core do not change.
- **Idempotent consumers**: `functions/aggregate_consumer.py` documents the
  Phase 7 contract — dedupe on `event_id`, dead-letter poison messages,
  deterministic scoring.
- **Leaderboard scale**: a Memorystore sorted set gives O(log n) updates/reads;
  a periodic Firestore snapshot provides durability without Firestore fan-out.
- **Consent-first mobile**: Fit/Maps capture is strictly opt-in; no background
  location without explicit user permission.
