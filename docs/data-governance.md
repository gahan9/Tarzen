<!-- SPDX-License-Identifier: MIT -->

# Data governance

How the platform classifies, minimizes, retains, and partitions data. The
guiding principle is **data minimization**: persist only what the product needs,
never raw free text, and keep analytics aggregate-only so an individual's
activity cannot be reconstructed from the warehouse.

## Event taxonomy

| Event | Emitted by | Schema | Sink | Purpose |
|-------|-----------|--------|------|---------|
| `request_completed` (access log) | `api/logging_middleware.py` | `{request_id, trace_id, uid, route, method, status, latency_ms, llm_used, gemini_latency_ms}` | Cloud Logging | Observability / SLOs; **no bodies, no PII text** |
| `FootprintLogRecord` (durable log) | `adapters/firestore.py` | `{uid, domain, mode, kg_co2e, request_id, created_at}` | Firestore `footprint_logs` | Per-user history (data-minimized) |
| `FootprintEvent` (domain event) | `adapters/pubsub.py` | `{event_id, uid, domain, mode, kg_co2e, request_id, occurred_at}` | Pub/Sub `footprint-events` | Async aggregation / gamification (Phase 7) |
| `AggregateRow` (analytics) | `adapters/bigquery.py` | `{event_date, domain, mode, total_kg_co2e, event_count}` | BigQuery `carbon_analytics` | Aggregate-only analytics; **no per-user id, no text** |

## PII classification

| Field | Classification | Handling |
|-------|----------------|----------|
| `uid` (Firebase user id) | Pseudonymous identifier | Stored in Firestore + Pub/Sub event; logged in access log; **never** exported to BigQuery; never in error payloads |
| `domain`, `mode` | Non-identifying activity metadata | Stored and aggregated freely |
| `kg_co2e`, `distance_km`, `passengers` | Non-identifying measurements | Stored/aggregated; bounded at the schema (`models/schemas.py`) |
| `request_id`, `trace_id` | Correlation ids (non-PII) | Logged and stored for tracing |
| Credentials / service-account key | Secret | `SecretStr` (`core/config.py`); Secret Manager at runtime; never logged/returned |
| Free-text / location | Not collected in MVP | Mobile Fit/Maps capture is opt-in & consented only (Phase 9) |

## Retention & TTL

| Store | Default retention | Mechanism |
|-------|-------------------|-----------|
| Firestore `footprint_logs` | Rolling user history (recommended TTL: 24 months) | Firestore TTL policy on `created_at` (apply in deployment) |
| Pub/Sub `footprint-events` | 7 days (broker default) + dead-letter after max delivery attempts | Subscription config; `event_id` dedupe for replay safety |
| BigQuery `carbon_analytics` | Long-lived (aggregate, non-PII) | Partition-expiration optional; safe to keep (no PII) |
| Cloud Logging | Per project log-bucket retention (e.g. 30 days) | Logging config; bodies never logged |
| `processed_events` (Phase 7 dedupe) | Short TTL (e.g. 7 days, ≥ Pub/Sub retention) | Firestore TTL keyed by `event_id` |

## BigQuery partitioning & clustering

- **Partition** by `event_date` (ingestion/date column) so analytical scans and
  Looker Studio dashboards prune to a date range and stay cheap.
- **Cluster** by `domain` (then `mode`) so per-domain rollups read only relevant
  blocks.
- Rows are **aggregate-only** (`AggregateRow`): summed `total_kg_co2e` and
  `event_count` per `(event_date, domain, mode)` bucket — no `uid`, no raw text.

## Firestore data-minimization

- The log record (`FootprintLogRecord`) carries the minimum fields for product
  features; there is no free-text or sensitive-category field.
- Writes are best-effort and isolated (`api/routes.py:_log_footprint`) so a
  storage hiccup never blocks or corrupts the user response.
- Roadmap denormalized aggregates (streaks/points/rank) are designed as
  single-doc reads to scale dashboards without fan-out (see `phases.md`).

## Access control (least privilege)

The Cloud Run runtime service account (`infra/terraform/main.tf`) holds only:
`datastore.user` (Firestore), `aiplatform.user` (Vertex), `pubsub.publisher` on
the single `footprint-events` topic, `bigquery.dataEditor` scoped to the one
`carbon_analytics` dataset, and `secretmanager.secretAccessor`. No project-wide
editor/owner grants.
