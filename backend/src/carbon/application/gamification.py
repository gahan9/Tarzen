# SPDX-License-Identifier: MIT
"""Server-side gamification scoring (points, streaks, badges).

Scoring is pure and deterministic and derives **only** from server-validated
footprint events and the user's persisted state — never from client-supplied
points — which is the anti-cheat guarantee. The same (state, event) pair always
yields the same result, so a replayed event produces no double counting when the
caller gates on the processed-event ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from carbon.adapters.progress_store import UserProgress
from carbon.adapters.pubsub import FootprintEvent

_BASE_POINTS = 10
_STREAK_BONUS_PER_DAY = 2
_STREAK_BONUS_CAP_DAYS = 7

# Lifetime-points tiers (id -> threshold) and streak milestones (id -> days).
_POINT_BADGES: tuple[tuple[str, int], ...] = (
    ("bronze", 100),
    ("silver", 500),
    ("gold", 1000),
)
_STREAK_BADGES: tuple[tuple[str, int], ...] = (
    ("week_warrior", 7),
    ("fortnight_hero", 14),
)


@dataclass(frozen=True, slots=True)
class ScoreDelta:
    """The scoring outcome of processing a single event.

    Attributes:
        uid: The user the delta applies to.
        points_awarded: Points granted for the event.
        streak_days: The user's streak length after this event.
        badges_unlocked: Newly unlocked badge ids (empty if none).
    """

    uid: str
    points_awarded: int
    streak_days: int
    badges_unlocked: tuple[str, ...]


def _event_date(event: FootprintEvent) -> date:
    """Extract the calendar date from an event's ISO-8601 timestamp."""
    return datetime.fromisoformat(event.occurred_at).date()


class GamificationService:
    """Computes points/streaks/badges from footprint events (pure)."""

    def apply(
        self, state: UserProgress, event: FootprintEvent
    ) -> tuple[UserProgress, ScoreDelta]:
        """Apply an event to a user's state, returning the new state and delta.

        Pure and deterministic: identical inputs always produce identical
        outputs. Same-day repeats earn base points but do not advance the
        streak; a one-day gap continues it; a larger gap resets it.

        Args:
            state: The user's persisted state before this event.
            event: A server-emitted, validated footprint event.

        Returns:
            A tuple of the updated :class:`UserProgress` and the
            :class:`ScoreDelta` describing what changed.
        """
        event_day = _event_date(event)
        streak, is_new_day = self._next_streak(state, event_day)

        points_awarded = _BASE_POINTS
        if is_new_day:
            points_awarded += _STREAK_BONUS_PER_DAY * min(
                streak, _STREAK_BONUS_CAP_DAYS
            )

        new_points = state.points + points_awarded
        last_active = self._next_last_active(state, event_day, is_new_day)

        unlocked = self._newly_unlocked(state.badges, new_points, streak)
        new_badges = tuple(sorted(set(state.badges) | set(unlocked)))

        new_state = replace(
            state,
            points=new_points,
            streak_days=streak,
            last_active_date=last_active.isoformat(),
            badges=new_badges,
        )
        delta = ScoreDelta(
            uid=state.uid,
            points_awarded=points_awarded,
            streak_days=streak,
            badges_unlocked=unlocked,
        )
        return new_state, delta

    @staticmethod
    def _next_streak(state: UserProgress, event_day: date) -> tuple[int, bool]:
        """Compute the post-event streak and whether a new day was counted."""
        if state.last_active_date is None:
            return 1, True
        last = date.fromisoformat(state.last_active_date)
        if event_day == last:
            return state.streak_days, False
        if event_day < last:  # out-of-order replay; do not advance or reset
            return state.streak_days, False
        if event_day == last + timedelta(days=1):
            return state.streak_days + 1, True
        return 1, True  # gap > 1 day resets the streak

    @staticmethod
    def _next_last_active(
        state: UserProgress, event_day: date, is_new_day: bool
    ) -> date:
        """Resolve the last-active date, never moving it backwards."""
        if state.last_active_date is None:
            return event_day
        last = date.fromisoformat(state.last_active_date)
        if is_new_day and event_day > last:
            return event_day
        return last

    @staticmethod
    def _newly_unlocked(
        existing: tuple[str, ...], points: int, streak: int
    ) -> tuple[str, ...]:
        """Return badge ids crossed by this event that were not held before."""
        held = set(existing)
        unlocked: list[str] = []
        for badge_id, threshold in _POINT_BADGES:
            if points >= threshold and badge_id not in held:
                unlocked.append(badge_id)
        for badge_id, threshold in _STREAK_BADGES:
            if streak >= threshold and badge_id not in held:
                unlocked.append(badge_id)
        return tuple(unlocked)
