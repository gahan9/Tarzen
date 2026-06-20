# SPDX-License-Identifier: MIT
"""Idempotency and decoding tests for the aggregate consumer."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

import pytest

from carbon.adapters.bigquery import AggregateRow
from carbon.adapters.progress_store import InMemoryGamificationStateStore
from carbon.adapters.pubsub import FootprintEvent
from carbon.application.gamification import GamificationService
from carbon.functions import aggregate_consumer as ac
from carbon.functions.aggregate_consumer import (
    AggregateConsumer,
    MessageDecodeError,
    build_aggregate_row,
    decode_message,
    extract_message_data,
)


class FakeExporter:
    """In-memory analytics exporter recording aggregate rows."""

    def __init__(self) -> None:
        self.rows: list[AggregateRow] = []

    async def export_aggregate(self, row: AggregateRow) -> None:
        self.rows.append(row)


@dataclass
class FakeCloudEvent:
    """Minimal CloudEvent stand-in carrying a Pub/Sub envelope."""

    data: object


def _event(eid: str = "e1", *, kg: float = 8.0) -> FootprintEvent:
    return FootprintEvent(
        event_id=eid,
        uid="user-1",
        domain="transport",
        mode="car",
        kg_co2e=kg,
        request_id="r1",
        occurred_at="2026-01-01T08:00:00+00:00",
    )


def _build_consumer() -> tuple[
    AggregateConsumer, InMemoryGamificationStateStore, FakeExporter
]:
    store = InMemoryGamificationStateStore()
    exporter = FakeExporter()
    consumer = AggregateConsumer(
        state_store=store,
        exporter=exporter,
        gamification=GamificationService(),
    )
    return consumer, store, exporter


async def test_handle_new_event_scores_and_exports() -> None:
    """A first-seen event applies scoring and exports one aggregate row."""
    consumer, store, exporter = _build_consumer()

    delta = await consumer.handle(_event())

    assert delta is not None
    assert delta.points_awarded == 12
    assert store.states["user-1"].points == 12
    assert len(exporter.rows) == 1
    assert exporter.rows[0].total_kg_co2e == 8.0
    assert exporter.rows[0].event_count == 1


async def test_replayed_event_is_idempotent() -> None:
    """Reprocessing the same event id changes nothing (replay-safe)."""
    consumer, store, exporter = _build_consumer()

    first = await consumer.handle(_event(eid="dup"))
    second = await consumer.handle(_event(eid="dup"))

    assert first is not None
    assert second is None
    assert store.states["user-1"].points == 12  # applied exactly once
    assert len(exporter.rows) == 1  # exported exactly once


async def test_distinct_events_accumulate() -> None:
    """Two distinct events both apply and both export."""
    consumer, store, exporter = _build_consumer()

    await consumer.handle(_event(eid="a"))
    await consumer.handle(_event(eid="b"))

    assert store.states["user-1"].points == 22  # 12 + 10 (same-day repeat)
    assert len(exporter.rows) == 2


async def test_consume_decodes_then_handles() -> None:
    """consume() decodes a JSON payload and processes it."""
    consumer, store, _ = _build_consumer()
    payload = json.dumps(
        {
            "event_id": "c1",
            "uid": "user-1",
            "domain": "transport",
            "mode": "car",
            "kg_co2e": 5.0,
            "request_id": "r1",
            "occurred_at": "2026-01-01T08:00:00+00:00",
        }
    )

    delta = await consumer.consume(payload)

    assert delta is not None
    assert store.states["user-1"].points == 12


def test_build_aggregate_row_strips_identifiers() -> None:
    """The aggregate row carries only date/domain/mode/total/count."""
    row = build_aggregate_row(_event(kg=3.5))
    assert row == AggregateRow(
        event_date="2026-01-01",
        domain="transport",
        mode="car",
        total_kg_co2e=3.5,
        event_count=1,
    )


def test_decode_message_rejects_invalid_json() -> None:
    """Malformed JSON raises MessageDecodeError."""
    with pytest.raises(MessageDecodeError):
        decode_message("not json")


def test_decode_message_rejects_missing_fields() -> None:
    """A JSON object missing required fields raises MessageDecodeError."""
    with pytest.raises(MessageDecodeError):
        decode_message(json.dumps({"event_id": "x"}))


def test_extract_message_data_decodes_base64() -> None:
    """A well-formed Pub/Sub CloudEvent yields the decoded body bytes."""
    body = b'{"hello": "world"}'
    event = FakeCloudEvent(
        data={"message": {"data": base64.b64encode(body).decode("ascii")}}
    )
    assert extract_message_data(event) == body


def test_extract_message_data_rejects_malformed_envelope() -> None:
    """A CloudEvent without a message mapping raises MessageDecodeError."""
    with pytest.raises(MessageDecodeError):
        extract_message_data(FakeCloudEvent(data={"nope": 1}))


def test_main_requires_configuration() -> None:
    """main() raises until a consumer is configured."""
    ac._consumer = None
    with pytest.raises(RuntimeError):
        ac.main(FakeCloudEvent(data={}))


def test_main_runs_configured_consumer() -> None:
    """main() decodes the envelope and drives the configured consumer."""
    consumer, store, exporter = _build_consumer()
    ac.configure(consumer)
    try:
        body = json.dumps(
            {
                "event_id": "m1",
                "uid": "user-1",
                "domain": "transport",
                "mode": "car",
                "kg_co2e": 4.0,
                "request_id": "r1",
                "occurred_at": "2026-01-01T08:00:00+00:00",
            }
        ).encode("utf-8")
        event = FakeCloudEvent(
            data={"message": {"data": base64.b64encode(body).decode("ascii")}}
        )
        ac.main(event)
    finally:
        ac._consumer = None

    assert store.states["user-1"].points == 12
    assert len(exporter.rows) == 1
