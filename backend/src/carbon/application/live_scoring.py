# SPDX-License-Identifier: MIT
"""Synchronous, replay-safe live scoring for the savings request path.

The Phase 7 Pub/Sub consumer that would score events asynchronously is still a
stub, so to make points and leaderboards *live* this service reuses the
already-tested pure :class:`~carbon.application.gamification.GamificationService`
and :class:`~carbon.application.leaderboard.LeaderboardService` directly in the
request path. It stays correct under retries by gating on the same
processed-event ledger the async consumer uses: a replayed ``event_id`` mutates
nothing. The leaderboard is updated with the user's server-derived lifetime
points (never client-supplied), keyed by their anonymous handle.
"""

from __future__ import annotations

from dataclasses import dataclass

from carbon.adapters.progress_store import GamificationStateStore, UserProgress
from carbon.adapters.pubsub import FootprintEvent
from carbon.application.gamification import GamificationService, ScoreDelta
from carbon.application.leaderboard import LeaderboardService


@dataclass(frozen=True, slots=True)
class ScoringOutcome:
    """The result of applying an event to a user's live score.

    Attributes:
        state: The user's persisted state after scoring.
        delta: What the event changed (points, streak, badges).
        replayed: ``True`` if the event was already processed (no mutation).
    """

    state: UserProgress
    delta: ScoreDelta
    replayed: bool


class LiveScorer:
    """Applies gamification scoring and updates leaderboards in the request path."""

    def __init__(
        self,
        *,
        state_store: GamificationStateStore,
        gamification: GamificationService,
        leaderboard: LeaderboardService | None = None,
    ) -> None:
        """Initialise with the state store and the pure scoring services.

        The leaderboard is optional: when it is not wired (for example before a
        Memorystore backend is provisioned), points and streaks are still scored
        and persisted; only the board update is skipped.
        """
        self._state_store = state_store
        self._gamification = gamification
        self._leaderboard = leaderboard

    async def score(
        self, event: FootprintEvent, *, member: str, boards: tuple[str, ...]
    ) -> ScoringOutcome:
        """Score one event exactly once and publish the score to leaderboards.

        Args:
            event: A server-built, validated footprint/savings event.
            member: The anonymous handle to rank on the leaderboards.
            boards: Board keys to update with the user's new lifetime points
                (e.g. the regional and global boards).

        Returns:
            The :class:`ScoringOutcome`. For a replayed event the current state
            and a zero-points delta are returned and nothing is mutated.
        """
        if await self._state_store.is_processed(event.event_id):
            state = await self._state_store.get_state(event.uid)
            zero = ScoreDelta(
                uid=event.uid,
                points_awarded=0,
                streak_days=state.streak_days,
                badges_unlocked=(),
            )
            return ScoringOutcome(state=state, delta=zero, replayed=True)

        state = await self._state_store.get_state(event.uid)
        new_state, delta = self._gamification.apply(state, event)
        await self._state_store.apply_update(new_state, event.event_id)
        if self._leaderboard is not None:
            for board in boards:
                await self._leaderboard.submit_score(
                    board, member, float(new_state.points)
                )
        return ScoringOutcome(state=new_state, delta=delta, replayed=False)
