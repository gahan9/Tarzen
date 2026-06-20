# SPDX-License-Identifier: MIT
"""Tests for the Firestore-backed gamification state store (fake client)."""

from __future__ import annotations

from typing import Any

from carbon.adapters.progress_store import (
    FirestoreGamificationStateStore,
    UserProgress,
)


class _FakeSnap:
    def __init__(self, data: dict[str, Any] | None) -> None:
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any] | None:
        return self._data


class _FakeDoc:
    def __init__(self, bucket: dict[str, dict[str, Any]], key: str) -> None:
        self._bucket = bucket
        self._key = key

    def get(self) -> _FakeSnap:
        return _FakeSnap(self._bucket.get(self._key))

    def set(self, data: dict[str, Any]) -> None:
        self._bucket[self._key] = data


class _FakeCollection:
    def __init__(self, bucket: dict[str, dict[str, Any]]) -> None:
        self._bucket = bucket

    def document(self, key: str) -> _FakeDoc:
        return _FakeDoc(self._bucket, key)


class FakeFirestore:
    """Minimal in-memory Firestore client stand-in."""

    def __init__(self) -> None:
        self._cols: dict[str, dict[str, dict[str, Any]]] = {}

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self._cols.setdefault(name, {}))


async def test_zero_state_for_unseen_user() -> None:
    """An unseen user reads back as a fresh zero-state."""
    store = FirestoreGamificationStateStore(FakeFirestore())
    state = await store.get_state("new-user")
    assert state == UserProgress(uid="new-user")


async def test_apply_update_persists_and_marks_processed() -> None:
    """apply_update round-trips state and records the event as processed."""
    store = FirestoreGamificationStateStore(FakeFirestore())
    progress = UserProgress(
        uid="user-1",
        points=42,
        streak_days=3,
        last_active_date="2026-01-03",
        badges=("bronze",),
    )

    assert await store.is_processed("e1") is False
    await store.apply_update(progress, "e1")

    assert await store.is_processed("e1") is True
    assert await store.get_state("user-1") == progress
