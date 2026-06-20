# SPDX-License-Identifier: MIT
"""Leaderboard service: ranks, percentiles, resets, and durable snapshots.

Coordinates the sorted-set store (friends/teams/global rank queries) and the
durable snapshot store (weekly-challenge archival + restore). Boards are plain
string keys, so the same logic serves a global board, a per-team board, or a
friends board scoped by the caller.
"""

from __future__ import annotations

from carbon.adapters.leaderboard_store import (
    LeaderboardSnapshotStore,
    LeaderboardStore,
    RankEntry,
)


class LeaderboardService:
    """Server-side leaderboard coordination over injected ports."""

    def __init__(
        self,
        store: LeaderboardStore,
        *,
        snapshot_store: LeaderboardSnapshotStore | None = None,
    ) -> None:
        """Initialise with a sorted-set store and an optional snapshot store."""
        self._store = store
        self._snapshot_store = snapshot_store

    async def submit_score(self, board: str, member: str, score: float) -> None:
        """Record a member's score on a board (O(log n) update)."""
        await self._store.add_score(board, member, score)

    async def get_rank(self, board: str, member: str) -> RankEntry | None:
        """Return a member's current rank entry, or ``None`` if absent."""
        return await self._store.get_rank(board, member)

    async def get_top(self, board: str, count: int) -> list[RankEntry]:
        """Return the top ``count`` ranked entries."""
        return await self._store.top(board, count)

    async def get_percentile(self, board: str, member: str) -> float | None:
        """Return the member's percentile rank (0-100), or ``None`` if absent.

        The percentile is the share of other members the player outranks: the
        top player on a populated board is at 100.0 and the bottom at 0.0. A
        sole member is defined as 100.0.
        """
        entry = await self._store.get_rank(board, member)
        if entry is None:
            return None
        total = await self._store.count(board)
        if total <= 1:
            return 100.0
        better_than = total - 1 - entry.rank
        return round(better_than / (total - 1) * 100, 2)

    async def rank_among(self, board: str, members: list[str]) -> list[RankEntry]:
        """Return a re-ranked board restricted to ``members`` (friends/teams).

        Members are ordered by their global standing on ``board`` but re-indexed
        0..n-1 so the result is a standalone friends/teams leaderboard. Members
        absent from the board are omitted.
        """
        wanted = set(members)
        present = [e for e in await self._store.snapshot(board) if e.member in wanted]
        return [
            RankEntry(member=entry.member, score=entry.score, rank=index)
            for index, entry in enumerate(present)
        ]

    async def snapshot(self, board: str) -> list[RankEntry]:
        """Persist the board's current ordering to the durable snapshot store.

        Returns:
            The entries that were snapshotted.

        Raises:
            RuntimeError: If no snapshot store was configured.
        """
        entries = await self._store.snapshot(board)
        await self._require_snapshot_store().save(board, entries)
        return entries

    async def restore(self, board: str) -> list[RankEntry]:
        """Reload a board from its durable snapshot into the sorted-set store.

        Returns:
            The restored entries.

        Raises:
            RuntimeError: If no snapshot store was configured.
        """
        entries = await self._require_snapshot_store().load(board)
        await self._store.reset(board)
        for entry in entries:
            await self._store.add_score(board, entry.member, entry.score)
        return entries

    async def reset_weekly(self, board: str) -> list[RankEntry]:
        """Archive then clear a board — the Cloud Scheduler weekly-reset hook.

        Returns:
            The archived entries (empty if the board had no members).

        Raises:
            RuntimeError: If no snapshot store was configured.
        """
        archived = await self._store.snapshot(board)
        await self._require_snapshot_store().save(f"{board}:archive", archived)
        await self._store.reset(board)
        return archived

    def _require_snapshot_store(self) -> LeaderboardSnapshotStore:
        """Return the snapshot store or fail clearly if it is unconfigured."""
        if self._snapshot_store is None:
            raise RuntimeError("leaderboard snapshot store is not configured")
        return self._snapshot_store
