# SPDX-License-Identifier: MIT
"""Deterministic scoring tests for the gamification service."""

from __future__ import annotations

from carbon.adapters.progress_store import UserProgress
from carbon.adapters.pubsub import FootprintEvent
from carbon.application.gamification import GamificationService


def _event(day: str, *, eid: str = "e1", kg: float = 5.0) -> FootprintEvent:
    """Build a footprint event occurring on ``day`` (YYYY-MM-DD)."""
    return FootprintEvent(
        event_id=eid,
        uid="user-1",
        domain="transport",
        mode="car",
        kg_co2e=kg,
        request_id="r1",
        occurred_at=f"{day}T08:00:00+00:00",
    )


def test_first_event_starts_streak_and_awards_base_plus_bonus() -> None:
    """A user's first event starts a 1-day streak and awards base + bonus."""
    svc = GamificationService()
    state, delta = svc.apply(UserProgress(uid="user-1"), _event("2026-01-01"))

    assert delta.streak_days == 1
    assert delta.points_awarded == 12  # 10 base + 2 * min(1, 7)
    assert state.points == 12
    assert state.last_active_date == "2026-01-01"


def test_consecutive_day_extends_streak() -> None:
    """An event on the next day extends the streak and scales the bonus."""
    svc = GamificationService()
    s1, _ = svc.apply(UserProgress(uid="user-1"), _event("2026-01-01", eid="a"))
    s2, delta = svc.apply(s1, _event("2026-01-02", eid="b"))

    assert delta.streak_days == 2
    assert delta.points_awarded == 14  # 10 + 2 * 2
    assert s2.points == 26


def test_same_day_repeat_awards_base_only_no_streak_advance() -> None:
    """A second event the same day earns base points but no streak/bonus."""
    svc = GamificationService()
    s1, _ = svc.apply(UserProgress(uid="user-1"), _event("2026-01-01", eid="a"))
    s2, delta = svc.apply(s1, _event("2026-01-01", eid="b"))

    assert delta.streak_days == 1
    assert delta.points_awarded == 10
    assert s2.points == 22


def test_gap_resets_streak() -> None:
    """A gap of more than one day resets the streak to 1."""
    svc = GamificationService()
    s1, _ = svc.apply(UserProgress(uid="user-1"), _event("2026-01-01", eid="a"))
    s2, delta = svc.apply(s1, _event("2026-01-05", eid="b"))

    assert delta.streak_days == 1
    assert delta.points_awarded == 12


def test_out_of_order_event_does_not_change_streak_or_date() -> None:
    """An older replayed-date event does not move the streak or last date back."""
    svc = GamificationService()
    s1, _ = svc.apply(UserProgress(uid="user-1"), _event("2026-01-02", eid="a"))
    s2, delta = svc.apply(s1, _event("2026-01-01", eid="b"))

    assert s2.last_active_date == "2026-01-02"
    assert delta.streak_days == 1
    assert delta.points_awarded == 10


def test_scoring_is_deterministic() -> None:
    """Identical (state, event) inputs always produce identical outputs."""
    svc = GamificationService()
    base = UserProgress(
        uid="user-1", points=40, streak_days=3, last_active_date="2026-01-03"
    )
    ev = _event("2026-01-04")
    first = svc.apply(base, ev)
    second = svc.apply(base, ev)

    assert first == second


def test_point_badge_unlocks_once_at_threshold() -> None:
    """Crossing a points threshold unlocks the tier badge exactly once."""
    svc = GamificationService()
    state = UserProgress(
        uid="user-1", points=92, streak_days=2, last_active_date="2026-01-01"
    )
    new_state, delta = svc.apply(state, _event("2026-01-02"))  # 92 + 14 = 106

    assert "bronze" in delta.badges_unlocked
    assert "bronze" in new_state.badges

    # A subsequent event must not re-award the already-held badge.
    _, delta2 = svc.apply(new_state, _event("2026-01-03", eid="c"))
    assert "bronze" not in delta2.badges_unlocked


def test_streak_badge_unlocks_at_seven_days() -> None:
    """Reaching a 7-day streak unlocks the week_warrior badge."""
    svc = GamificationService()
    state = UserProgress(
        uid="user-1", points=10, streak_days=6, last_active_date="2026-01-06"
    )
    _, delta = svc.apply(state, _event("2026-01-07"))

    assert delta.streak_days == 7
    assert "week_warrior" in delta.badges_unlocked
