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

# A defensive upper bound on a single logged distance (~2.5x Earth's
# circumference) — large enough for long-haul round trips, small enough to
# reject obviously bogus or abusive values.
MAX_DISTANCE_KM = 100_000.0
MAX_PASSENGERS = 1_000


class FootprintRequest(BaseModel):
    """Request body for a footprint calculation."""

    model_config = ConfigDict(extra="forbid")

    domain: str = Field(min_length=1, examples=["transport"])
    mode: TransportMode = Field(examples=["car"])
    distance_km: float = Field(ge=0, le=MAX_DISTANCE_KM, examples=[42.0])
    passengers: int = Field(default=1, ge=1, le=MAX_PASSENGERS, examples=[1])


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
