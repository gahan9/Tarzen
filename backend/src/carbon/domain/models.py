# SPDX-License-Identifier: MIT
"""Pure domain value objects shared across trackers and the insight engine.

These are framework-free dataclasses with no I/O or serialization concerns.
The API layer maps them to and from Pydantic models at the transport boundary.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BreakdownItem:
    """A single labelled contribution to a footprint total.

    Attributes:
        label: Human-readable description of the contribution.
        kg_co2e: Emissions attributed to this item, in kg CO2e.
    """

    label: str
    kg_co2e: float


@dataclass(frozen=True, slots=True)
class FootprintResult:
    """The deterministic result of a domain footprint calculation.

    Attributes:
        domain: The domain that produced this result (e.g. ``transport``).
        kg_co2e: Total personal emissions for the activity, in kg CO2e.
        breakdown: Ordered per-component contributions summing to ``kg_co2e``.
    """

    domain: str
    kg_co2e: float
    breakdown: tuple[BreakdownItem, ...]
