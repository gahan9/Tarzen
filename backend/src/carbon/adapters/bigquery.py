# SPDX-License-Identifier: MIT
"""BigQuery adapter for aggregate-only analytics export.

Only aggregate rows are exported — never raw user text or per-user identifiers —
so the analytics dataset cannot reconstruct an individual's activity.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from typing import Protocol

from google.cloud import bigquery


@dataclass(frozen=True, slots=True)
class AggregateRow:
    """An aggregate analytics row (no per-user identifiers).

    Attributes:
        event_date: Partition date (``YYYY-MM-DD``).
        domain: Footprint domain the aggregate covers.
        mode: Activity mode the aggregate covers.
        total_kg_co2e: Summed emissions for the bucket.
        event_count: Number of events in the bucket.
    """

    event_date: str
    domain: str
    mode: str
    total_kg_co2e: float
    event_count: int


class AnalyticsExporter(Protocol):
    """Port for exporting aggregate analytics rows."""

    async def export_aggregate(self, row: AggregateRow) -> None:
        """Export a single aggregate row."""
        ...


class BigQueryAnalyticsExporter:
    """BigQuery-backed :class:`AnalyticsExporter`."""

    def __init__(self, client: bigquery.Client, *, table_id: str) -> None:
        """Initialise with an injected BigQuery client and fully-qualified table."""
        self._client = client
        self._table_id = table_id

    async def export_aggregate(self, row: AggregateRow) -> None:
        """Insert the aggregate row off the event loop.

        Raises:
            RuntimeError: If BigQuery reports row-level insert errors.
        """
        await asyncio.to_thread(self._insert_sync, row)

    def _insert_sync(self, row: AggregateRow) -> None:
        """Blocking BigQuery insert executed in a worker thread."""
        errors = self._client.insert_rows_json(self._table_id, [asdict(row)])
        if errors:
            raise RuntimeError("bigquery insert reported row errors")
