# SPDX-License-Identifier: MIT
"""Leaderboard persistence: sorted-set store + durable snapshot store.

A sorted set gives O(log n) score updates and rank reads. The
:class:`LeaderboardStore` Protocol keeps the application layer independent of the
backend; two implementations are provided:

* :class:`InMemoryLeaderboardStore` — a pure-Python sorted set used by tests and
  local runs (no Redis needed). It defines the canonical ordering: descending
  score, ties broken by ascending member id.
* :class:`MemorystoreLeaderboardStore` — a Redis/Memorystore ZSET backend that
  reproduces the same ordering by storing negated scores so Redis' native
  ascending order yields highest-score-first with ascending-member tie-breaks.

:class:`LeaderboardSnapshotStore` persists a board's ordering durably (Firestore)
so it survives cache eviction and supports weekly-challenge archival/restore.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol

_REDIS_TIMEOUT_S = 5.0


@dataclass(frozen=True, slots=True)
class RankEntry:
    """A single leaderboard position.

    Attributes:
        member: The ranked member id (e.g. uid or team id).
        score: The member's score.
        rank: Zero-based rank (0 = top).
    """

    member: str
    score: float
    rank: int


class LeaderboardStore(Protocol):
    """Port for a sorted-set leaderboard backend."""

    async def add_score(self, board: str, member: str, score: float) -> None:
        """Insert or update ``member``'s score on ``board`` (O(log n))."""
        ...

    async def get_rank(self, board: str, member: str) -> RankEntry | None:
        """Return the member's current rank entry, or ``None`` if absent."""
        ...

    async def top(self, board: str, count: int) -> list[RankEntry]:
        """Return the top ``count`` entries in rank order."""
        ...

    async def count(self, board: str) -> int:
        """Return the number of members on ``board``."""
        ...

    async def snapshot(self, board: str) -> list[RankEntry]:
        """Return every entry on ``board`` in rank order."""
        ...

    async def reset(self, board: str) -> None:
        """Remove all members from ``board``."""
        ...


def _rank_entries(scores: dict[str, float]) -> list[RankEntry]:
    """Order members by descending score, breaking ties by ascending member id."""
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [
        RankEntry(member=member, score=score, rank=index)
        for index, (member, score) in enumerate(ordered)
    ]


@dataclass(slots=True)
class InMemoryLeaderboardStore:
    """Pure-Python sorted-set :class:`LeaderboardStore` for tests/local use."""

    boards: dict[str, dict[str, float]] = field(default_factory=dict)

    async def add_score(self, board: str, member: str, score: float) -> None:
        """Set the member's score on the board."""
        self.boards.setdefault(board, {})[member] = score

    async def get_rank(self, board: str, member: str) -> RankEntry | None:
        """Return the member's rank entry, or ``None`` if not present."""
        for entry in _rank_entries(self.boards.get(board, {})):
            if entry.member == member:
                return entry
        return None

    async def top(self, board: str, count: int) -> list[RankEntry]:
        """Return the top ``count`` ranked entries."""
        if count < 0:
            raise ValueError("count must be non-negative")
        return _rank_entries(self.boards.get(board, {}))[:count]

    async def count(self, board: str) -> int:
        """Return the number of members on the board."""
        return len(self.boards.get(board, {}))

    async def snapshot(self, board: str) -> list[RankEntry]:
        """Return all ranked entries on the board."""
        return _rank_entries(self.boards.get(board, {}))

    async def reset(self, board: str) -> None:
        """Clear all members from the board."""
        self.boards.pop(board, None)


class RedisLike(Protocol):
    """Structural type for the async Redis client methods used here."""

    async def zadd(self, name: str, mapping: dict[str, float]) -> int:
        """Add/update members with the given scores."""
        ...

    async def zrank(self, name: str, value: str) -> int | None:
        """Return the ascending-order rank of ``value``."""
        ...

    async def zscore(self, name: str, value: str) -> float | None:
        """Return the stored score of ``value``."""
        ...

    async def zrange(
        self, name: str, start: int, end: int, *, withscores: bool = False
    ) -> list[tuple[str, float]]:
        """Return members in ascending score order over ``[start, end]``."""
        ...

    async def zcard(self, name: str) -> int:
        """Return the number of members in the set."""
        ...

    async def delete(self, *names: str) -> int:
        """Delete the given keys."""
        ...


def _as_str(value: str | bytes) -> str:
    """Decode a possibly-bytes Redis member id to ``str``."""
    return value.decode("utf-8") if isinstance(value, bytes) else value


class MemorystoreLeaderboardStore:
    """Redis/Memorystore ZSET-backed :class:`LeaderboardStore`.

    Scores are stored negated so Redis' native ascending order (``ZRANGE`` /
    ``ZRANK``) yields highest-score-first with ascending-member tie-breaks,
    matching :class:`InMemoryLeaderboardStore`. Every call is bounded by a
    timeout to avoid hanging the event loop on a slow backend.
    """

    def __init__(self, client: RedisLike, *, timeout_s: float = _REDIS_TIMEOUT_S):
        """Initialise with an injected async Redis client."""
        self._client = client
        self._timeout_s = timeout_s

    async def add_score(self, board: str, member: str, score: float) -> None:
        """Upsert the member's (negated) score on the board."""
        await asyncio.wait_for(
            self._client.zadd(board, {member: -score}), timeout=self._timeout_s
        )

    async def get_rank(self, board: str, member: str) -> RankEntry | None:
        """Return the member's rank entry, or ``None`` if absent."""
        rank = await asyncio.wait_for(
            self._client.zrank(board, member), timeout=self._timeout_s
        )
        if rank is None:
            return None
        stored = await asyncio.wait_for(
            self._client.zscore(board, member), timeout=self._timeout_s
        )
        if stored is None:
            return None
        return RankEntry(member=member, score=-stored, rank=rank)

    async def top(self, board: str, count: int) -> list[RankEntry]:
        """Return the top ``count`` ranked entries."""
        if count <= 0:
            return []
        rows = await asyncio.wait_for(
            self._client.zrange(board, 0, count - 1, withscores=True),
            timeout=self._timeout_s,
        )
        return self._to_entries(rows)

    async def count(self, board: str) -> int:
        """Return the number of members on the board."""
        return await asyncio.wait_for(
            self._client.zcard(board), timeout=self._timeout_s
        )

    async def snapshot(self, board: str) -> list[RankEntry]:
        """Return all ranked entries on the board."""
        rows = await asyncio.wait_for(
            self._client.zrange(board, 0, -1, withscores=True),
            timeout=self._timeout_s,
        )
        return self._to_entries(rows)

    async def reset(self, board: str) -> None:
        """Delete the board key."""
        await asyncio.wait_for(self._client.delete(board), timeout=self._timeout_s)

    @staticmethod
    def _to_entries(rows: list[tuple[str, float]]) -> list[RankEntry]:
        """Map ``(member, -score)`` rows to ranked entries (un-negating score)."""
        return [
            RankEntry(member=_as_str(member), score=-stored, rank=index)
            for index, (member, stored) in enumerate(rows)
        ]


class LeaderboardSnapshotStore(Protocol):
    """Port for durable leaderboard snapshots (archival + restore)."""

    async def save(self, board: str, entries: list[RankEntry]) -> None:
        """Persist a full ordered snapshot of ``board``."""
        ...

    async def load(self, board: str) -> list[RankEntry]:
        """Return the most recent saved snapshot (empty if none)."""
        ...


@dataclass(slots=True)
class InMemoryLeaderboardSnapshotStore:
    """In-memory :class:`LeaderboardSnapshotStore` for tests/local use."""

    snapshots: dict[str, list[RankEntry]] = field(default_factory=dict)

    async def save(self, board: str, entries: list[RankEntry]) -> None:
        """Store a copy of the ordered snapshot."""
        self.snapshots[board] = list(entries)

    async def load(self, board: str) -> list[RankEntry]:
        """Return a copy of the stored snapshot, or an empty list."""
        return list(self.snapshots.get(board, []))


class FirestoreLeaderboardSnapshotStore:
    """Firestore-backed :class:`LeaderboardSnapshotStore`."""

    def __init__(
        self, client: object, *, collection: str = "leaderboard_snapshots"
    ) -> None:
        """Initialise with an injected Firestore client and collection name."""
        self._client = client
        self._collection = collection

    async def save(self, board: str, entries: list[RankEntry]) -> None:
        """Persist the snapshot as a single document off the event loop."""
        await asyncio.wait_for(
            asyncio.to_thread(self._save_sync, board, entries),
            timeout=_REDIS_TIMEOUT_S,
        )

    async def load(self, board: str) -> list[RankEntry]:
        """Read the snapshot document, returning an empty list if absent."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._load_sync, board), timeout=_REDIS_TIMEOUT_S
        )

    def _save_sync(self, board: str, entries: list[RankEntry]) -> None:
        """Blocking snapshot write."""
        rows = [{"member": e.member, "score": e.score, "rank": e.rank} for e in entries]
        self._client.collection(self._collection).document(  # type: ignore[attr-defined]
            board
        ).set({"entries": rows})

    def _load_sync(self, board: str) -> list[RankEntry]:
        """Blocking snapshot read mapped to :class:`RankEntry` objects."""
        doc = (
            self._client.collection(self._collection)  # type: ignore[attr-defined]
            .document(board)
            .get()
        )
        if not doc.exists:
            return []
        data = doc.to_dict() or {}
        return [
            RankEntry(
                member=str(row["member"]),
                score=float(row["score"]),
                rank=int(row["rank"]),
            )
            for row in data.get("entries", [])
        ]
