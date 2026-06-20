# SPDX-License-Identifier: MIT
"""Waste domain tracker (roadmap stub, Phase 6).

TODO(phase-6): Implement recycling/landfill footprint using versioned
waste-stream emission factors.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams


class WasteTracker:
    """Placeholder waste tracker implementing the DomainTracker port."""

    domain: ClassVar[str] = "waste"

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 6 lands.
        """
        raise NotImplementedError("waste tracker is a Phase 6 roadmap item")
