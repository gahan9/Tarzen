# SPDX-License-Identifier: MIT
"""Leaderboard service (roadmap stub, Phase 8).

Coordinates sorted-set rank updates and reads (friends/teams/global) over the
:class:`~carbon.adapters.leaderboard_store.LeaderboardStore` port, with periodic
durable snapshots to Firestore. Concrete logic lands in Phase 8.
"""

from __future__ import annotations

from carbon.adapters.leaderboard_store import LeaderboardStore, RankEntry


class LeaderboardService:
    """Server-side leaderboard coordination (roadmap stub)."""

    def __init__(self, store: LeaderboardStore) -> None:
        """Initialise with an injected leaderboard store port."""
        self._store = store

    async def submit_score(self, board: str, member: str, score: float) -> None:
        """Record a member's score on a board.

        Raises:
            NotImplementedError: Always, until Phase 8 lands.
        """
        raise NotImplementedError("leaderboard service is a Phase 8 roadmap item")

    async def get_rank(self, board: str, member: str) -> RankEntry | None:
        """Return a member's current rank entry.

        Raises:
            NotImplementedError: Always, until Phase 8 lands.
        """
        raise NotImplementedError("leaderboard service is a Phase 8 roadmap item")

    async def get_top(self, board: str, count: int) -> list[RankEntry]:
        """Return the top ``count`` ranked entries.

        Raises:
            NotImplementedError: Always, until Phase 8 lands.
        """
        raise NotImplementedError("leaderboard service is a Phase 8 roadmap item")
