# SPDX-License-Identifier: MIT
"""Firestore adapter for data-minimized per-user footprint logs.

Only the minimum fields needed for the product are persisted — no free-text or
sensitive personal data. The synchronous Firestore SDK is wrapped with
:func:`asyncio.to_thread` to keep the request path non-blocking.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Protocol

from google.cloud import firestore

DEFAULT_COLLECTION = "footprint_logs"


@dataclass(frozen=True, slots=True)
class FootprintLogRecord:
    """A data-minimized footprint log entry.

    Attributes:
        uid: Authenticated user id (owner of the log).
        domain: Footprint domain (e.g. ``transport``).
        mode: Activity mode (e.g. ``car``); not personally identifying.
        kg_co2e: Computed emissions for the activity.
        request_id: Correlation id for tracing.
        created_at: UTC ISO-8601 timestamp.
    """

    uid: str
    domain: str
    mode: str
    kg_co2e: float
    request_id: str
    created_at: str


def build_log_record(
    *, uid: str, domain: str, mode: str, kg_co2e: float, request_id: str
) -> FootprintLogRecord:
    """Construct a log record stamped with the current UTC time."""
    return FootprintLogRecord(
        uid=uid,
        domain=domain,
        mode=mode,
        kg_co2e=kg_co2e,
        request_id=request_id,
        created_at=datetime.now(UTC).isoformat(),
    )


class FootprintLogStore(Protocol):
    """Port for persisting a per-user footprint log."""

    async def write_log(self, record: FootprintLogRecord) -> None:
        """Persist a single footprint log entry."""
        ...


class FirestoreFootprintStore:
    """Firestore-backed :class:`FootprintLogStore`."""

    def __init__(
        self, client: firestore.Client, *, collection: str = DEFAULT_COLLECTION
    ) -> None:
        """Initialise with an injected Firestore client and collection name."""
        self._client = client
        self._collection = collection

    async def write_log(self, record: FootprintLogRecord) -> None:
        """Write the record to Firestore off the event loop."""
        await asyncio.to_thread(self._write_sync, record)

    def _write_sync(self, record: FootprintLogRecord) -> None:
        """Blocking Firestore write executed in a worker thread."""
        self._client.collection(self._collection).add(asdict(record))
