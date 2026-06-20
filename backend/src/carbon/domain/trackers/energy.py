# SPDX-License-Identifier: MIT
"""Energy domain tracker — electricity and natural gas by kWh.

Deterministic and pure: emissions are a versioned grid/fuel intensity factor
(kg CO2e per kWh) multiplied by the consumed kilowatt-hours. No I/O at call
time; the factor catalogue is loaded once and cached.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.factors import FactorCatalogue, get_factor_catalogue
from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams
from carbon.domain.trackers.scalar import compute_scalar


class EnergyTracker:
    """Deterministic energy emissions calculator (kWh-based)."""

    domain: ClassVar[str] = "energy"

    def __init__(self, catalogue: FactorCatalogue | None = None) -> None:
        """Initialise with an optional explicit factor catalogue (for tests)."""
        self._catalogue = catalogue or get_factor_catalogue()

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Compute an energy footprint from ``mode`` and ``kwh``.

        Args:
            params: Mapping with ``mode`` (e.g. ``electricity``) and ``kwh``
                (non-negative number of kilowatt-hours).

        Returns:
            The deterministic footprint for the energy use.

        Raises:
            InvalidInputError: If parameters are missing or malformed.
            UnsupportedModeError: If ``mode`` has no registered factor.
        """
        return compute_scalar(
            domain=self.domain,
            params=params,
            quantity_key="kwh",
            unit="kWh",
            catalogue=self._catalogue,
        )
