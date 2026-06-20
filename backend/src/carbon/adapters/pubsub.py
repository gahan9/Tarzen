# SPDX-License-Identifier: MIT
"""Pub/Sub adapter that publishes footprint events for async processing.

Publishing decouples the request path from downstream aggregation/gamification
(Cloud Functions consumers), so write spikes never block the user request.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Protocol

import google.cloud.pubsub_v1 as pubsub_v1


@dataclass(frozen=True, slots=True)
class FootprintEvent:
    """An event emitted when a footprint is logged.

    Attributes:
        event_id: Idempotency key for replay-safe consumers.
        uid: Authenticated user id.
        domain: Footprint domain.
        mode: Activity mode.
        kg_co2e: Computed emissions.
        request_id: Correlation id for tracing.
        occurred_at: UTC ISO-8601 timestamp.
    """

    event_id: str
    uid: str
    domain: str
    mode: str
    kg_co2e: float
    request_id: str
    occurred_at: str


def build_event(
    *,
    event_id: str,
    uid: str,
    domain: str,
    mode: str,
    kg_co2e: float,
    request_id: str,
) -> FootprintEvent:
    """Construct a footprint event stamped with the current UTC time."""
    return FootprintEvent(
        event_id=event_id,
        uid=uid,
        domain=domain,
        mode=mode,
        kg_co2e=kg_co2e,
        request_id=request_id,
        occurred_at=datetime.now(UTC).isoformat(),
    )


class EventPublisher(Protocol):
    """Port for publishing footprint events."""

    async def publish(self, event: FootprintEvent) -> str:
        """Publish an event and return the broker message id."""
        ...


class PubSubEventPublisher:
    """Pub/Sub-backed :class:`EventPublisher`."""

    def __init__(
        self, publisher: pubsub_v1.PublisherClient, *, topic_path: str
    ) -> None:
        """Initialise with an injected publisher client and topic path."""
        self._publisher = publisher
        self._topic_path = topic_path

    async def publish(self, event: FootprintEvent) -> str:
        """Publish the event off the event loop, returning the message id."""
        return await asyncio.to_thread(self._publish_sync, event)

    def _publish_sync(self, event: FootprintEvent) -> str:
        """Blocking Pub/Sub publish executed in a worker thread."""
        data = json.dumps(asdict(event)).encode("utf-8")
        future = self._publisher.publish(
            self._topic_path, data, event_id=event.event_id
        )
        return str(future.result())
