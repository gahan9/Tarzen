<!-- SPDX-License-Identifier: MIT -->

# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to
adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Backend hardening response headers (CSP, `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP/CORP,
  HSTS) applied to every response via middleware, with unit tests.
- Web app automated test suite: Vitest + Testing Library + jsdom with
  axe-based accessibility assertions, gated at 90% coverage.
- `CONTRIBUTING.md`, `.editorconfig`, and a `.pre-commit-config.yaml` running
  ruff, standard hygiene hooks, and gitleaks locally.

### Changed

- CI now gates the full stack: a frontend job (typecheck, ESLint/jsx-a11y,
  Vitest coverage, production build) and a mobile job (typecheck, jest) run
  alongside the existing backend, security, and commit-hygiene jobs.
- Backend coverage is now enforced at 90% (`fail_under`) instead of being
  report-only.

## [0.1.0] — 2026-06-14

### Added

- Hexagonal FastAPI backend: deterministic transport footprint engine,
  policy-gated insights (rule-based-first, Gemini for phrasing only with a
  prompt-injection guard), typed error envelope, Firebase auth, per-uid rate
  limiting, and `/healthz` + `/readyz` probes.
- Multi-domain trackers (transport, energy, food, shopping, waste) with
  golden-table unit tests behind a `DomainTracker` port and registry.
- Server-side gamification (points, streaks, badges; deterministic, anti-cheat)
  and leaderboard (ranking, percentiles, weekly reset, durable snapshots).
- Pub/Sub → Cloud Function → BigQuery aggregation pipeline with an idempotent,
  PII-stripping consumer.
- Vite + React web app and Expo offline-first mobile app (durable sync queue,
  consent gating, Firebase auth) sharing a zod `shared-types` API contract.
- Infrastructure as code (least-privilege Terraform, Cloud Build, non-root
  Docker image) and docs: architecture, threat model, data governance,
  phased roadmap, evaluation mapping, and committed OpenAPI contract.

[Unreleased]: https://github.com/gahan9/Tarzen/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gahan9/Tarzen/releases/tag/v0.1.0
