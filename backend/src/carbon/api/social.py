# SPDX-License-Identifier: MIT
"""Social read API: anonymous regional leaderboard and profile.

* ``GET /api/leaderboard?scope=region|global`` — the top anonymous handles for
  the caller's region cohort (or everyone), the caller's own standing, and
  rule-based level-up tips.
* ``GET /api/profile`` — the caller's anonymous, public-safe profile composed
  with their gamification state and lifetime saved total.

Identity never leaves the service: only the stable anonymous handle, a
decorative emoji, score, and rank are returned. Both endpoints fail closed with
a ``feature_unavailable`` 503 when their backing stores are not wired.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request

from carbon.adapters.leaderboard_store import RankEntry
from carbon.adapters.profile_store import emoji_for_handle
from carbon.api.auth import require_uid
from carbon.api.container import Dependencies
from carbon.api.errors import ApiError
from carbon.application.boards import board_for_scope, region_board
from carbon.application.gamification import level_up_tips
from carbon.models.schemas import (
    ErrorEnvelope,
    LeaderboardEntry,
    LeaderboardResponse,
    LeaderboardScope,
    ProfileResponse,
)

router = APIRouter(tags=["social"])


async def _member_handle(deps: Dependencies, uid: str, region: str) -> str:
    """Return the caller's leaderboard member id (anon handle, or uid)."""
    if deps.profile_store is None:
        return uid
    profile = await deps.profile_store.get_or_create(uid, region)
    return profile.anon_handle


@router.get(
    "/api/leaderboard",
    response_model=LeaderboardResponse,
    responses={401: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
)
async def get_leaderboard(
    request: Request,
    scope: Literal["region", "global"] = Query(default="global"),
    uid: str = Depends(require_uid),
) -> LeaderboardResponse:
    """Return the anonymous leaderboard for a scope plus the caller's standing."""
    deps: Dependencies = request.app.state.deps
    if deps.leaderboard is None:
        raise ApiError(
            503, "feature_unavailable", "The leaderboard is not available yet."
        )

    region = deps.region_resolver.resolve(request.headers)
    board = board_for_scope(scope, region)
    member = await _member_handle(deps, uid, region)

    top: list[RankEntry] = await deps.leaderboard.get_top(board, deps.leaderboard_top)
    my_entry = await deps.leaderboard.get_rank(board, member)
    percentile = await deps.leaderboard.get_percentile(board, member)

    entries = [
        LeaderboardEntry(
            anon_handle=entry.member,
            emoji=emoji_for_handle(entry.member),
            score=entry.score,
            rank=entry.rank,
            is_me=entry.member == member,
        )
        for entry in top
    ]

    tips: list[str] = []
    if deps.state_store is not None:
        state = await deps.state_store.get_state(uid)
        tips = list(level_up_tips(state))

    scope_value: LeaderboardScope = scope
    return LeaderboardResponse(
        scope=scope_value,
        region=region if scope == "region" else None,
        entries=entries,
        my_rank=my_entry.rank if my_entry is not None else None,
        percentile=percentile,
        tips=tips,
    )


@router.get(
    "/api/profile",
    response_model=ProfileResponse,
    responses={401: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
)
async def get_profile(
    request: Request,
    uid: str = Depends(require_uid),
) -> ProfileResponse:
    """Return the caller's anonymous profile and gamification state."""
    deps: Dependencies = request.app.state.deps
    if deps.profile_store is None or deps.state_store is None:
        raise ApiError(503, "feature_unavailable", "Profiles are not available yet.")

    region = deps.region_resolver.resolve(request.headers)
    profile = await deps.profile_store.get_or_create(uid, region)
    state = await deps.state_store.get_state(uid)

    my_rank: int | None = None
    percentile: float | None = None
    if deps.leaderboard is not None:
        board = region_board(profile.region)
        entry = await deps.leaderboard.get_rank(board, profile.anon_handle)
        my_rank = entry.rank if entry is not None else None
        percentile = await deps.leaderboard.get_percentile(
            board, profile.anon_handle
        )

    return ProfileResponse(
        anon_handle=profile.anon_handle,
        emoji=profile.emoji,
        region=profile.region,
        points=state.points,
        streak_days=state.streak_days,
        badges=list(state.badges),
        total_kg_co2e_saved=profile.total_kg_co2e_saved,
        my_rank=my_rank,
        percentile=percentile,
    )
