# SPDX-License-Identifier: MIT
"""Pydantic request/response models and the typed error envelope.

These models define the public wire contract for ``POST /api/footprint`` and
mirror the schema consumed by the frontend worker. Field bounds reject invalid
input at the transport boundary before any domain logic runs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransportMode = Literal["car", "bus", "rail", "flight"]
EnergyMode = Literal["electricity", "natural_gas"]
FoodMode = Literal[
    "beef_meal",
    "pork_meal",
    "chicken_meal",
    "fish_meal",
    "vegetarian_meal",
    "vegan_meal",
]
ShoppingMode = Literal["clothing", "electronics", "furniture", "general_goods"]
WasteMode = Literal["landfill", "recycling", "composting"]
# Closed union of every supported activity mode; unknown modes are rejected at
# the boundary. New domains extend this union — the domain core is untouched.
FootprintMode = TransportMode | EnergyMode | FoodMode | ShoppingMode | WasteMode

# Defensive upper bounds per activity unit — large enough for legitimate use,
# small enough to reject obviously bogus or abusive values. The distance bound
# is ~2.5x Earth's circumference.
MAX_DISTANCE_KM = 100_000.0
MAX_PASSENGERS = 1_000
MAX_KWH = 1_000_000.0
MAX_SERVINGS = 100
MAX_SPEND = 10_000_000.0
MAX_WASTE_KG = 1_000_000.0


class FootprintRequest(BaseModel):
    """Request body for a footprint calculation.

    A single ``mode`` plus exactly one activity quantity describes the activity.
    The transport contract (``distance_km`` + ``passengers``) is preserved; new
    domains add their own optional quantity field (``kwh``, ``servings``,
    ``spend``, ``waste_kg``). The tracker for the requested domain validates
    that the quantity it needs is present.
    """

    model_config = ConfigDict(extra="forbid")

    domain: str = Field(min_length=1, examples=["transport"])
    mode: FootprintMode = Field(examples=["car"])
    distance_km: float | None = Field(
        default=None, ge=0, le=MAX_DISTANCE_KM, examples=[42.0]
    )
    passengers: int = Field(default=1, ge=1, le=MAX_PASSENGERS, examples=[1])
    kwh: float | None = Field(default=None, ge=0, le=MAX_KWH, examples=[120.0])
    servings: int | None = Field(default=None, ge=0, le=MAX_SERVINGS, examples=[2])
    spend: float | None = Field(default=None, ge=0, le=MAX_SPEND, examples=[50.0])
    waste_kg: float | None = Field(default=None, ge=0, le=MAX_WASTE_KG, examples=[3.0])


class BreakdownItem(BaseModel):
    """A labelled contribution to the footprint total."""

    label: str
    kg_co2e: float


class Insight(BaseModel):
    """Human-friendly framing of a footprint result."""

    message: str
    benchmark: str
    actions: list[str]
    needs_context: bool
    llm_used: bool


class FootprintResponse(BaseModel):
    """Successful response for a footprint calculation."""

    kg_co2e: float
    breakdown: list[BreakdownItem]
    insight: Insight
    request_id: str


class ErrorDetail(BaseModel):
    """Machine-readable error detail carried inside the envelope."""

    code: str
    message: str
    request_id: str


class ErrorEnvelope(BaseModel):
    """Top-level error envelope returned for every failed request."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Carbon savings, leaderboard, and profile contracts
#
# These mirror the merged frontend zod contract in ``packages/shared-types``.
# The frontend strips unknown keys, but field names below match it exactly.
# ---------------------------------------------------------------------------

# Low-carbon mode that produced a saving: carpooling, or transit replacing a
# solo car trip. Closed union — unknown modes are rejected at the boundary.
SavingsMode = Literal["carpool", "bus", "rail"]
# Provenance of a savings entry. ``ticket`` is the only server-verified source
# and is set by the API (never the client) after a receipt is parsed.
SavingsSource = Literal["manual", "import", "ticket"]
LeaderboardScope = Literal["region", "global"]

MAX_IMPORT_ROWS = 500


class SavingsRequest(BaseModel):
    """Request body for a single manual/carpool savings entry."""

    model_config = ConfigDict(extra="forbid")

    source: SavingsSource = Field(default="manual", examples=["manual"])
    mode: SavingsMode = Field(examples=["carpool"])
    distance_km: float = Field(ge=0, le=MAX_DISTANCE_KM, examples=[12.0])
    passengers: int = Field(default=1, ge=1, le=MAX_PASSENGERS, examples=[3])


class CarpoolImportRow(BaseModel):
    """One row of a CSV/trip-history carpool import (carpool is implied)."""

    model_config = ConfigDict(extra="forbid")

    date: str | None = Field(default=None, examples=["2026-06-01"])
    distance_km: float = Field(ge=0, le=MAX_DISTANCE_KM, examples=[18.5])
    passengers: int = Field(default=1, ge=1, le=MAX_PASSENGERS, examples=[2])


class SavingsImportRequest(BaseModel):
    """Request body for a batch carpool import."""

    model_config = ConfigDict(extra="forbid")

    rows: list[CarpoolImportRow] = Field(min_length=1, max_length=MAX_IMPORT_ROWS)


class SavingsResponse(BaseModel):
    """Successful response for a single savings entry.

    Points/streak/badges are server-authoritative (never client-supplied).
    """

    kg_co2e_saved: float
    verified: bool
    points_awarded: int
    badges_unlocked: list[str]
    streak_days: int
    request_id: str


class SavingsImportResponse(BaseModel):
    """Successful response for a batch carpool import."""

    total_kg_co2e_saved: float
    rows_imported: int
    points_awarded: int
    badges_unlocked: list[str]
    streak_days: int
    request_id: str


class TicketExtraction(BaseModel):
    """Best-effort fields a vision model extracts from a transit ticket.

    Every field is optional: an illegible receipt may yield only some of them.
    """

    origin: str | None = None
    destination: str | None = None
    mode: SavingsMode | None = None
    date: str | None = None
    fare: float | None = None


class TicketResponse(BaseModel):
    """Verified-ticket response — the savings result plus what was read."""

    kg_co2e_saved: float
    verified: bool
    points_awarded: int
    badges_unlocked: list[str]
    streak_days: int
    request_id: str
    extraction: TicketExtraction | None = None


class LeaderboardEntry(BaseModel):
    """A single ranked, anonymised competitor."""

    anon_handle: str
    emoji: str | None = None
    score: float
    rank: int
    is_me: bool = False


class LeaderboardResponse(BaseModel):
    """Anonymous leaderboard view with the caller's standing and tips."""

    scope: LeaderboardScope
    region: str | None = None
    entries: list[LeaderboardEntry]
    my_rank: int | None = None
    percentile: float | None = None
    tips: list[str]


class ProfileResponse(BaseModel):
    """The caller's anonymous, public-safe profile and gamification state."""

    anon_handle: str
    emoji: str | None = None
    region: str | None = None
    points: int
    streak_days: int
    badges: list[str]
    total_kg_co2e_saved: float
    my_rank: int | None = None
    percentile: float | None = None
