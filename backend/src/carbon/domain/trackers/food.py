# SPDX-License-Identifier: MIT
"""Food domain tracker — diet/meal categories by servings.

Deterministic and pure: emissions are a versioned per-meal emission factor
(kg CO2e per serving) multiplied by the number of servings. Categories range
from beef to vegan, ordered by typical intensity.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.factors import FactorCatalogue, get_factor_catalogue
from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams
from carbon.domain.trackers.scalar import compute_scalar


class FoodTracker:
    """Deterministic food emissions calculator (meal-serving based)."""

    domain: ClassVar[str] = "food"

    def __init__(self, catalogue: FactorCatalogue | None = None) -> None:
        """Initialise with an optional explicit factor catalogue (for tests)."""
        self._catalogue = catalogue or get_factor_catalogue()

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Compute a food footprint from ``mode`` and ``servings``.

        Args:
            params: Mapping with ``mode`` (e.g. ``beef_meal``) and ``servings``
                (non-negative integer count of meals).

        Returns:
            The deterministic footprint for the meals.

        Raises:
            InvalidInputError: If parameters are missing or malformed.
            UnsupportedModeError: If ``mode`` has no registered factor.
        """
        return compute_scalar(
            domain=self.domain,
            params=params,
            quantity_key="servings",
            unit="servings",
            catalogue=self._catalogue,
            require_int=True,
        )
