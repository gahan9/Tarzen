# SPDX-License-Identifier: MIT
"""Waste domain tracker — landfill, recycling, and composting by mass.

Deterministic and pure: emissions are a versioned waste-stream emission factor
(kg CO2e per kg of waste) multiplied by the disposed mass.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.factors import FactorCatalogue, get_factor_catalogue
from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams
from carbon.domain.trackers.scalar import compute_scalar


class WasteTracker:
    """Deterministic waste emissions calculator (mass-based)."""

    domain: ClassVar[str] = "waste"

    def __init__(self, catalogue: FactorCatalogue | None = None) -> None:
        """Initialise with an optional explicit factor catalogue (for tests)."""
        self._catalogue = catalogue or get_factor_catalogue()

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Compute a waste footprint from ``mode`` and ``waste_kg``.

        Args:
            params: Mapping with ``mode`` (e.g. ``landfill``) and ``waste_kg``
                (non-negative mass in kilograms).

        Returns:
            The deterministic footprint for the disposal.

        Raises:
            InvalidInputError: If parameters are missing or malformed.
            UnsupportedModeError: If ``mode`` has no registered factor.
        """
        return compute_scalar(
            domain=self.domain,
            params=params,
            quantity_key="waste_kg",
            unit="kg",
            catalogue=self._catalogue,
        )
