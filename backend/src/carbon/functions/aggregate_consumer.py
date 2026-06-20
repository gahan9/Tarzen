# SPDX-License-Identifier: MIT
"""Idempotent Pub/Sub consumer that aggregates footprint events.

Pub/Sub delivers at-least-once, so this consumer is replay-safe: it gates every
event on a processed-event ledger keyed by ``event_id``. For a new event it
applies deterministic gamification scoring to the user's Firestore-backed state
and appends an aggregate-only row to BigQuery; a replay short-circuits and
mutates nothing.

The consumer depends only on ports, so unit tests drive it with in-memory fakes
and never touch the network. ``main`` is the Cloud Functions (gen2) entry point.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
from dataclasses import dataclass

from carbon.adapters.bigquery import AggregateRow, AnalyticsExporter
from carbon.adapters.progress_store import GamificationStateStore
from carbon.adapters.pubsub import FootprintEvent
from carbon.application.gamification import GamificationService, ScoreDelta

_LOGGER = logging.getLogger(__name__)


class MessageDecodeError(ValueError):
    """Raised when a Pub/Sub payload cannot be decoded into an event."""


def decode_message(data: bytes | str) -> FootprintEvent:
    """Decode a JSON Pub/Sub payload into a :class:`FootprintEvent`.

    Args:
        data: The raw message body (UTF-8 JSON), as bytes or str.

    Returns:
        The parsed event.

    Raises:
        MessageDecodeError: If the payload is not valid JSON or is missing
            required fields.
    """
    try:
        raw = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MessageDecodeError("payload is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise MessageDecodeError("payload must be a JSON object")
    try:
        return FootprintEvent(
            event_id=str(raw["event_id"]),
            uid=str(raw["uid"]),
            domain=str(raw["domain"]),
            mode=str(raw["mode"]),
            kg_co2e=float(raw["kg_co2e"]),
            request_id=str(raw["request_id"]),
            occurred_at=str(raw["occurred_at"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MessageDecodeError("payload missing required event fields") from exc


def build_aggregate_row(event: FootprintEvent) -> AggregateRow:
    """Project an event onto a per-day, per-mode aggregate row (no identifiers)."""
    event_date = event.occurred_at[:10]
    return AggregateRow(
        event_date=event_date,
        domain=event.domain,
        mode=event.mode,
        total_kg_co2e=event.kg_co2e,
        event_count=1,
    )


def extract_message_data(cloud_event: object) -> bytes:
    """Extract the raw message body from a Cloud Functions Pub/Sub CloudEvent.

    Args:
        cloud_event: An object exposing ``.data`` shaped as
            ``{"message": {"data": "<base64>"}}`` (gen2 Pub/Sub trigger).

    Returns:
        The decoded message body bytes.

    Raises:
        MessageDecodeError: If the envelope is malformed.
    """
    payload = getattr(cloud_event, "data", None)
    if not isinstance(payload, dict):
        raise MessageDecodeError("cloud event has no data mapping")
    message = payload.get("message")
    if not isinstance(message, dict) or "data" not in message:
        raise MessageDecodeError("cloud event message is malformed")
    try:
        return base64.b64decode(message["data"])
    except (binascii.Error, ValueError) as exc:
        raise MessageDecodeError("message data is not valid base64") from exc


@dataclass(slots=True)
class AggregateConsumer:
    """Replay-safe processor for footprint events."""

    state_store: GamificationStateStore
    exporter: AnalyticsExporter
    gamification: GamificationService

    async def handle(self, event: FootprintEvent) -> ScoreDelta | None:
        """Process one event exactly once.

        Returns ``None`` for a replay (already-processed) event; otherwise
        applies scoring, persists state (which records the event as processed),
        exports the aggregate row, and returns the score delta.

        State is persisted before the aggregate export so that a crash between
        the two cannot double-count points or aggregates on redelivery — at the
        cost of, at worst, a single dropped aggregate row (a tolerable trade for
        an awareness metric).
        """
        if await self.state_store.is_processed(event.event_id):
            _LOGGER.info(
                "aggregate_event_replay_skipped", extra={"eid": event.event_id}
            )
            return None

        state = await self.state_store.get_state(event.uid)
        new_state, delta = self.gamification.apply(state, event)
        await self.state_store.apply_update(new_state, event.event_id)
        await self.exporter.export_aggregate(build_aggregate_row(event))
        return delta

    async def consume(self, data: bytes | str) -> ScoreDelta | None:
        """Decode a raw Pub/Sub payload and process it."""
        return await self.handle(decode_message(data))


_consumer: AggregateConsumer | None = None


def configure(consumer: AggregateConsumer) -> None:
    """Install the consumer used by :func:`main` (called at deploy/startup)."""
    global _consumer
    _consumer = consumer


def main(cloud_event: object) -> None:
    """Cloud Functions (gen2) Pub/Sub entry point.

    Raises:
        RuntimeError: If no consumer has been configured via :func:`configure`.
        MessageDecodeError: If the event envelope or payload is malformed.
    """
    if _consumer is None:
        raise RuntimeError("aggregate consumer is not configured")
    data = extract_message_data(cloud_event)
    asyncio.run(_consumer.consume(data))
