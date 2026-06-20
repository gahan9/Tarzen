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
