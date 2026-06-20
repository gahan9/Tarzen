# SPDX-License-Identifier: MIT
"""Cloud Function: footprint-event aggregation consumer (roadmap stub).

Contract (Phase 7):
    Trigger:
        Pub/Sub topic ``footprint-events`` (CloudEvent, push subscription).
    Payload:
        Base64-encoded JSON matching ``carbon.adapters.pubsub.FootprintEvent``:
        ``{event_id, uid, domain, mode, kg_co2e, request_id, occurred_at}``.
    Idempotency:
        ``event_id`` is the dedupe key. The consumer MUST be replay-safe — record
        processed ``event_id`` values (e.g. a Firestore ``processed_events`` doc
        keyed by id with a TTL) and no-op on duplicates so at-least-once delivery
        cannot double-count.
    Effects (all server-side, no client trust):
        1. Upsert per-user daily aggregates -> Firestore (streaks, points totals).
        2. Append an aggregate row -> BigQuery (partitioned by date, clustered by
           domain); never write raw user text.
        3. Update gamification scores via the server-side scoring service.
    Guarantees:
        Deterministic scoring; failures are retried by Pub/Sub; poison messages
        go to a dead-letter topic after max delivery attempts.
"""

from __future__ import annotations

from typing import Any


def handle_footprint_event(cloud_event: Any) -> None:
    """Aggregate a single footprint event idempotently.

    Args:
        cloud_event: The CloudEvent delivered by the Pub/Sub trigger; its
            ``data["message"]["data"]`` is base64-encoded ``FootprintEvent`` JSON.

    Raises:
        NotImplementedError: Always, until Phase 7 lands.
    """
    raise NotImplementedError("aggregate consumer is a Phase 7 roadmap item")
