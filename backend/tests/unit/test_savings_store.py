# SPDX-License-Identifier: MIT
"""Tests for the savings store: in-memory dedupe + Firestore (fake client)."""

from __future__ import annotations

import asyncio
from typing import Any

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import firestore

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

    def create(self, data: dict[str, Any]) -> None:
        """Write only if absent, mirroring Firestore's atomic ``create``."""
        if self._key in self._bucket:
            raise AlreadyExists(self._key)  # type: ignore[no-untyped-call]
        self._bucket[self._key] = dict(data)

    def update(self, data: dict[str, Any]) -> None:
        """Merge fields into an existing doc, applying ``Increment`` sentinels."""
        existing = self._bucket.get(self._key)
        if existing is None:
            raise NotFound(self._key)  # type: ignore[no-untyped-call]
        merged = dict(existing)
        for key, value in data.items():
            if isinstance(value, firestore.Increment):
                base = merged.get(key, 0)
                merged[key] = base + value.value
            else:
                merged[key] = value
        self._bucket[self._key] = merged


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


async def test_in_memory_reserve_is_one_shot() -> None:
    """The first reservation of a hash wins; later ones for the same key fail."""
    store = InMemorySavingsStore()

    assert await store.try_reserve_image("u1", "h1") is True
    assert await store.try_reserve_image("u1", "h1") is False
    # A different user reusing the same hash is independent.
    assert await store.try_reserve_image("u2", "h1") is True


async def test_in_memory_reserve_is_atomic_under_concurrency() -> None:
    """Concurrent reservations of one hash yield exactly one winner."""
    store = InMemorySavingsStore()

    results = await asyncio.gather(
        *(store.try_reserve_image("u1", "dupe") for _ in range(20))
    )

    assert sum(1 for reserved in results if reserved) == 1
    assert len(store.seen_hashes) == 1


async def test_firestore_write_and_atomic_reserve() -> None:
    """Firestore store writes records and reserves a hash exactly once."""
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

    assert await store.try_reserve_image("u1", "abc") is True
    # A second attempt hits AlreadyExists from ``create`` and reports a dupe.
    assert await store.try_reserve_image("u1", "abc") is False
