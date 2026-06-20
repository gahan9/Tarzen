# SPDX-License-Identifier: MIT
"""Leaderboard store + service tests (in-memory and fake-Redis backends)."""

from __future__ import annotations

import pytest

from carbon.adapters.leaderboard_store import (
    FirestoreLeaderboardSnapshotStore,
    InMemoryLeaderboardSnapshotStore,
    InMemoryLeaderboardStore,
    MemorystoreLeaderboardStore,
    RankEntry,
)
from carbon.application.leaderboard import LeaderboardService
from tests.unit.test_progress_store import FakeFirestore

_BOARD = "global"


async def _seed(store: InMemoryLeaderboardStore) -> None:
    """Populate a board with four distinct scores."""
    await store.add_score(_BOARD, "alice", 100.0)
    await store.add_score(_BOARD, "bob", 80.0)
    await store.add_score(_BOARD, "carol", 60.0)
    await store.add_score(_BOARD, "dave", 40.0)


async def test_rank_order_is_descending_by_score() -> None:
    """Top entries are ordered from highest score to lowest, rank 0 first."""
    store = InMemoryLeaderboardStore()
    await _seed(store)

    top = await store.top(_BOARD, 10)

    assert [e.member for e in top] == ["alice", "bob", "carol", "dave"]
    assert [e.rank for e in top] == [0, 1, 2, 3]


async def test_score_update_moves_member() -> None:
    """Updating a score re-positions the member (O(log n) upsert)."""
    store = InMemoryLeaderboardStore()
    await _seed(store)

    await store.add_score(_BOARD, "dave", 200.0)
    entry = await store.get_rank(_BOARD, "dave")

    assert entry is not None
    assert entry.rank == 0
    assert entry.score == 200.0


async def test_stable_tie_break_by_member_id() -> None:
    """Equal scores break by ascending member id (deterministic, stable)."""
    store = InMemoryLeaderboardStore()
    await store.add_score(_BOARD, "zeta", 50.0)
    await store.add_score(_BOARD, "alpha", 50.0)
    await store.add_score(_BOARD, "mike", 50.0)

    order = [e.member for e in await store.top(_BOARD, 10)]

    assert order == ["alpha", "mike", "zeta"]


async def test_percentile_spans_zero_to_hundred() -> None:
    """Percentile is 100 for the top member and 0 for the bottom."""
    store = InMemoryLeaderboardStore()
    await _seed(store)
    svc = LeaderboardService(store)

    assert await svc.get_percentile(_BOARD, "alice") == 100.0
    assert await svc.get_percentile(_BOARD, "bob") == pytest.approx(66.67)
    assert await svc.get_percentile(_BOARD, "dave") == 0.0
    assert await svc.get_percentile(_BOARD, "ghost") is None


async def test_single_member_percentile_is_hundred() -> None:
    """A sole member is defined to be at the 100th percentile."""
    store = InMemoryLeaderboardStore()
    await store.add_score(_BOARD, "solo", 10.0)
    svc = LeaderboardService(store)

    assert await svc.get_percentile(_BOARD, "solo") == 100.0


async def test_rank_among_friends_reindexes() -> None:
    """A friends subset is re-ranked 0..n by global standing."""
    store = InMemoryLeaderboardStore()
    await _seed(store)
    svc = LeaderboardService(store)

    friends = await svc.rank_among(_BOARD, ["dave", "alice", "ghost"])

    assert [(e.member, e.rank) for e in friends] == [("alice", 0), ("dave", 1)]


async def test_snapshot_then_restore_round_trip() -> None:
    """A board survives a snapshot -> reset -> restore round trip intact."""
    store = InMemoryLeaderboardStore()
    snapshots = InMemoryLeaderboardSnapshotStore()
    await _seed(store)
    svc = LeaderboardService(store, snapshot_store=snapshots)

    before = await store.snapshot(_BOARD)
    await svc.snapshot(_BOARD)
    await store.reset(_BOARD)
    assert await store.count(_BOARD) == 0

    restored = await svc.restore(_BOARD)
    after = await store.snapshot(_BOARD)

    assert after == before
    assert restored == before


async def test_reset_weekly_archives_and_clears() -> None:
    """The weekly reset hook archives the board then clears it."""
    store = InMemoryLeaderboardStore()
    snapshots = InMemoryLeaderboardSnapshotStore()
    await _seed(store)
    svc = LeaderboardService(store, snapshot_store=snapshots)

    archived = await svc.reset_weekly(_BOARD)

    assert [e.member for e in archived] == ["alice", "bob", "carol", "dave"]
    assert await store.count(_BOARD) == 0
    assert await snapshots.load(f"{_BOARD}:archive") == archived


async def test_snapshot_without_store_raises() -> None:
    """Snapshot/restore require a configured snapshot store."""
    svc = LeaderboardService(InMemoryLeaderboardStore())
    with pytest.raises(RuntimeError):
        await svc.snapshot(_BOARD)


async def test_top_negative_count_rejected() -> None:
    """A negative count is rejected by the in-memory store."""
    store = InMemoryLeaderboardStore()
    with pytest.raises(ValueError):
        await store.top(_BOARD, -1)


class FakeRedis:
    """Minimal async Redis ZSET stand-in matching real ordering semantics."""

    def __init__(self) -> None:
        self._sets: dict[str, dict[str, float]] = {}

    async def zadd(self, name: str, mapping: dict[str, float]) -> int:
        bucket = self._sets.setdefault(name, {})
        added = sum(1 for m in mapping if m not in bucket)
        bucket.update(mapping)
        return added

    def _ordered(self, name: str) -> list[tuple[str, float]]:
        # Redis orders ascending by score, ties ascending by member id.
        return sorted(self._sets.get(name, {}).items(), key=lambda kv: (kv[1], kv[0]))

    async def zrank(self, name: str, value: str) -> int | None:
        for index, (member, _score) in enumerate(self._ordered(name)):
            if member == value:
                return index
        return None

    async def zscore(self, name: str, value: str) -> float | None:
        return self._sets.get(name, {}).get(value)

    async def zrange(
        self, name: str, start: int, end: int, *, withscores: bool = False
    ) -> list[tuple[str, float]]:
        ordered = self._ordered(name)
        stop = len(ordered) if end == -1 else end + 1
        return ordered[start:stop]

    async def zcard(self, name: str) -> int:
        return len(self._sets.get(name, {}))

    async def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            removed += 1 if self._sets.pop(name, None) is not None else 0
        return removed


async def test_memorystore_store_matches_canonical_ordering() -> None:
    """The Redis ZSET adapter reproduces descending-score/ascending-member order."""
    store = MemorystoreLeaderboardStore(FakeRedis())
    await store.add_score(_BOARD, "alice", 100.0)
    await store.add_score(_BOARD, "bob", 80.0)
    await store.add_score(_BOARD, "tie_b", 80.0)

    top = await store.top(_BOARD, 10)

    assert [e.member for e in top] == ["alice", "bob", "tie_b"]
    assert top[0] == RankEntry(member="alice", score=100.0, rank=0)
    assert await store.count(_BOARD) == 3

    bob = await store.get_rank(_BOARD, "bob")
    assert bob is not None and bob.score == 80.0 and bob.rank == 1
    assert await store.get_rank(_BOARD, "ghost") is None

    await store.reset(_BOARD)
    assert await store.count(_BOARD) == 0
    assert await store.top(_BOARD, 0) == []


async def test_memorystore_snapshot_returns_all() -> None:
    """snapshot() returns every entry in rank order from the ZSET backend."""
    store = MemorystoreLeaderboardStore(FakeRedis())
    await store.add_score(_BOARD, "a", 10.0)
    await store.add_score(_BOARD, "b", 20.0)

    snap = await store.snapshot(_BOARD)
    assert [e.member for e in snap] == ["b", "a"]


async def test_firestore_snapshot_store_round_trip() -> None:
    """The Firestore snapshot adapter persists and reloads entries."""
    snap_store = FirestoreLeaderboardSnapshotStore(FakeFirestore())
    entries = [
        RankEntry(member="alice", score=100.0, rank=0),
        RankEntry(member="bob", score=80.0, rank=1),
    ]

    assert await snap_store.load(_BOARD) == []
    await snap_store.save(_BOARD, entries)
    assert await snap_store.load(_BOARD) == entries
