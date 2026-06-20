# SPDX-License-Identifier: MIT
"""Shopping domain tracker — spend-based emissions by category.

Deterministic and pure: emissions are a versioned spend-to-emissions factor
(kg CO2e per GBP) multiplied by the amount spent in a goods category. Uses
order-of-magnitude environmentally-extended input-output (EEIO) factors.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.factors import FactorCatalogue, get_factor_catalogue
from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams
from carbon.domain.trackers.scalar import compute_scalar


class ShoppingTracker:
    """Deterministic shopping emissions calculator (spend-based)."""

    domain: ClassVar[str] = "shopping"

    def __init__(self, catalogue: FactorCatalogue | None = None) -> None:
        """Initialise with an optional explicit factor catalogue (for tests)."""
        self._catalogue = catalogue or get_factor_catalogue()

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Compute a shopping footprint from ``mode`` and ``spend``.

        Args:
            params: Mapping with ``mode`` (e.g. ``clothing``) and ``spend``
                (non-negative amount in GBP).

        Returns:
            The deterministic footprint for the purchase.

        Raises:
            InvalidInputError: If parameters are missing or malformed.
            UnsupportedModeError: If ``mode`` has no registered factor.
        """
        return compute_scalar(
            domain=self.domain,
            params=params,
            quantity_key="spend",
            unit="GBP",
            catalogue=self._catalogue,
        )
