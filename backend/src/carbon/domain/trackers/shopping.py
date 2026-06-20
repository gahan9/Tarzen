# SPDX-License-Identifier: MIT
"""Shopping domain tracker (roadmap stub, Phase 6).

TODO(phase-6): Implement goods/spend-based footprint using versioned
spend-to-emissions factors.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams


class ShoppingTracker:
    """Placeholder shopping tracker implementing the DomainTracker port."""

    domain: ClassVar[str] = "shopping"

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 6 lands.
        """
        raise NotImplementedError("shopping tracker is a Phase 6 roadmap item")
