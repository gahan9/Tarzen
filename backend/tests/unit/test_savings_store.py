# SPDX-License-Identifier: MIT
"""Tests for the savings store: in-memory dedupe + Firestore (fake client)."""

from __future__ import annotations

from typing import Any

from carbon.adapters.savings_store import (
    FirestoreSavingsStore,
    InMemorySavingsStore,
    build_savings_record,
)


class _Snap:
    def __init__(self, data: dict[str, Any] | None) -> None:
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return self._data


class _Doc:
    def __init__(self, bucket: dict[str, dict[str, Any]], key: str) -> None:
        self._bucket = bucket
        self._key = key

    def get(self) -> _Snap:
        return _Snap(self._bucket.get(self._key))

    def set(self, data: dict[str, Any]) -> None:
        self._bucket[self._key] = dict(data)


class _Query:
    def __init__(self, snaps: list[_Snap]) -> None:
        self._snaps = snaps

    def limit(self, count: int) -> _Query:
        return _Query(self._snaps[:count])

    def get(self) -> list[_Snap]:
        return list(self._snaps)


class _Collection:
    def __init__(self, bucket: dict[str, dict[str, Any]]) -> None:
        self._bucket = bucket

    def document(self, key: str) -> _Doc:
        return _Doc(self._bucket, key)

    def add(self, data: dict[str, Any]) -> None:
        self._bucket[f"auto-{len(self._bucket)}"] = dict(data)

    def where(self, field: str, _op: str, value: Any) -> _Query:
        snaps = [_Snap(d) for d in self._bucket.values() if d.get(field) == value]
        return _Query(snaps)


class RichFakeFirestore:
    """In-memory Firestore stand-in supporting document, add, and where."""

    def __init__(self) -> None:
        self._cols: dict[str, dict[str, dict[str, Any]]] = {}

    def collection(self, name: str) -> _Collection:
        return _Collection(self._cols.setdefault(name, {}))

    def bucket(self, name: str) -> dict[str, dict[str, Any]]:
        """Expose a collection's raw bucket for assertions."""
        return self._cols.setdefault(name, {})


async def test_in_memory_dedupe_roundtrip() -> None:
    """An image hash is duplicate only after it has been reserved."""
    store = InMemorySavingsStore()

    assert await store.is_duplicate_image("u1", "h1") is False
    await store.reserve_image("u1", "h1")
    assert await store.is_duplicate_image("u1", "h1") is True
    assert await store.is_duplicate_image("u2", "h1") is False


async def test_firestore_write_and_dedupe() -> None:
    """Firestore store writes records and tracks dedupe markers."""
    fake = RichFakeFirestore()
    store = FirestoreSavingsStore(fake)
    record = build_savings_record(
        uid="u1",
        source="ticket",
        mode="rail",
        distance_km=50.0,
        kg_co2e_saved=6.76,
        verified=True,
        request_id="r1",
        image_hash="abc",
    )

    await store.write_record(record)
    assert len(fake.bucket("savings_records")) == 1

    assert await store.is_duplicate_image("u1", "abc") is False
    await store.reserve_image("u1", "abc")
    assert await store.is_duplicate_image("u1", "abc") is True
