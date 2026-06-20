# SPDX-License-Identifier: MIT
"""Food domain tracker (roadmap stub, Phase 6).

TODO(phase-6): Implement diet/meal-category footprint using versioned per-meal
emission factors.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams


class FoodTracker:
    """Placeholder food tracker implementing the DomainTracker port."""

    domain: ClassVar[str] = "food"

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 6 lands.
        """
        raise NotImplementedError("food tracker is a Phase 6 roadmap item")
