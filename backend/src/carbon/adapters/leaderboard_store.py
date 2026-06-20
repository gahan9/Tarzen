# SPDX-License-Identifier: MIT
"""Leaderboard store port + Memorystore (Redis ZSET) stub (roadmap, Phase 8).

A sorted-set backend gives O(log n) rank updates and range reads. The port keeps
the application layer independent of Redis; the concrete adapter is a Phase 8
roadmap item.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


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


class MemorystoreLeaderboardStore:
    """Redis ZSET-backed :class:`LeaderboardStore` (roadmap stub, Phase 8)."""

    def __init__(self, client: object) -> None:
        """Initialise with an injected Redis client (typed in Phase 8)."""
        self._client = client

    async def add_score(self, board: str, member: str, score: float) -> None:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 8 lands.
        """
        raise NotImplementedError("leaderboard store is a Phase 8 roadmap item")

    async def get_rank(self, board: str, member: str) -> RankEntry | None:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 8 lands.
        """
        raise NotImplementedError("leaderboard store is a Phase 8 roadmap item")

    async def top(self, board: str, count: int) -> list[RankEntry]:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 8 lands.
        """
        raise NotImplementedError("leaderboard store is a Phase 8 roadmap item")
