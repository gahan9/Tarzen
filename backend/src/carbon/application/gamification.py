# SPDX-License-Identifier: MIT
"""Gamification service (roadmap stub, Phase 7).

Server-side scoring only: points, streaks, and badges are computed from
authenticated, server-emitted footprint events — never trusted from the client —
to resist cheating. Concrete logic lands in Phase 7.
"""

from __future__ import annotations

from dataclasses import dataclass

from carbon.adapters.pubsub import FootprintEvent


@dataclass(frozen=True, slots=True)
class ScoreDelta:
    """The scoring outcome of processing a single event.

    Attributes:
        uid: The user the delta applies to.
        points_awarded: Points granted for the event.
        streak_days: The user's streak length after this event.
        badges_unlocked: Newly unlocked badge ids.
    """

    uid: str
    points_awarded: int
    streak_days: int
    badges_unlocked: tuple[str, ...]


class GamificationService:
    """Computes points/streaks/badges from footprint events (roadmap stub)."""

    def score_event(self, event: FootprintEvent) -> ScoreDelta:
        """Compute the score delta for a footprint event.

        Args:
            event: A server-emitted footprint event.

        Returns:
            The :class:`ScoreDelta` to persist.

        Raises:
            NotImplementedError: Always, until Phase 7 lands.
        """
        raise NotImplementedError("gamification scoring is a Phase 7 roadmap item")
