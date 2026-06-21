# SPDX-License-Identifier: MIT
"""Leaderboard board-key conventions shared by the write and read paths.

Boards are plain string keys so one service serves both a global board and any
number of regional cohorts. Keeping the key derivation in one place ensures the
savings endpoints write to exactly the boards the leaderboard endpoint reads.
"""

from __future__ import annotations

_PREFIX = "savings"
GLOBAL_BOARD = f"{_PREFIX}:global"


def region_board(region: str) -> str:
    """Return the board key for a region cohort (``global`` maps to global)."""
    if region == "global":
        return GLOBAL_BOARD
    return f"{_PREFIX}:{region}"


def boards_for(region: str) -> tuple[str, ...]:
    """Return the de-duplicated boards a saving in ``region`` should update."""
    return tuple(dict.fromkeys((region_board(region), GLOBAL_BOARD)))


def board_for_scope(scope: str, region: str) -> str:
    """Return the board to read for a leaderboard ``scope`` (region or global)."""
    return region_board(region) if scope == "region" else GLOBAL_BOARD
