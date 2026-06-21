# SPDX-License-Identifier: MIT
"""Tests for synchronous, replay-safe live scoring."""

from __future__ import annotations

from carbon.adapters.leaderboard_store import InMemoryLeaderboardStore
from carbon.adapters.progress_store import InMemoryGamificationStateStore
from carbon.adapters.pubsub import build_event
from carbon.application.gamification import GamificationService
from carbon.application.leaderboard import LeaderboardService
from carbon.application.live_scoring import LiveScorer


def _scorer(
    state_store: InMemoryGamificationStateStore,
    leaderboard: LeaderboardService | None = None,
) -> LiveScorer:
    return LiveScorer(
        state_store=state_store,
        gamification=GamificationService(),
        leaderboard=leaderboard,
    )



async def test_replayed_event_does_not_double_count() -> None:
    """Re-scoring the same event id mutates nothing and awards zero points."""
    store = InMemoryGamificationStateStore()
    scorer = _scorer(store, LeaderboardService(InMemoryLeaderboardStore()))
    event = build_event(
        event_id="evt-1",
        uid="u1",
        domain="savings",
        mode="rail",
        kg_co2e=5.0,
        request_id="r1",
    )

    first = await scorer.score(event, member="Handle-1", boards=("savings:global",))
    second = await scorer.score(event, member="Handle-1", boards=("savings:global",))

    assert first.replayed is False
    assert first.delta.points_awarded == 12
    assert second.replayed is True
    assert second.delta.points_awarded == 0
    assert second.state.points == first.state.points



async def test_verified_event_earns_bonus_and_badge() -> None:
    """A verified event earns the verification bonus and the verified badge."""
    store = InMemoryGamificationStateStore()
    scorer = _scorer(store)
    event = build_event(
        event_id="evt-2",
        uid="u2",
        domain="savings",
        mode="rail",
        kg_co2e=5.0,
        request_id="r2",
        source="ticket",
        verified=True,
    )

    outcome = await scorer.score(event, member="Handle-2", boards=())

    assert outcome.delta.points_awarded == 27  # 12 + 15 verification bonus
    assert "verified_rider" in outcome.delta.badges_unlocked



async def test_scoring_without_leaderboard_still_persists_points() -> None:
    """Scoring works (points persist) even when no leaderboard is wired."""
    store = InMemoryGamificationStateStore()
    scorer = _scorer(store, leaderboard=None)
    event = build_event(
        event_id="evt-3",
        uid="u3",
        domain="savings",
        mode="bus",
        kg_co2e=2.0,
        request_id="r3",
    )

    outcome = await scorer.score(event, member="Handle-3", boards=("savings:global",))

    assert outcome.delta.points_awarded == 12
    assert (await store.get_state("u3")).points == 12
