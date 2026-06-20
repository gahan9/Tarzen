# SPDX-License-Identifier: MIT
"""Energy domain tracker (roadmap stub, Phase 6).

TODO(phase-6): Implement electricity/gas footprint from kWh or billed usage
using versioned grid-intensity factors, mirroring TransportTracker's structure.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.models import FootprintResult
from carbon.domain.ports import TrackerParams


class EnergyTracker:
    """Placeholder energy tracker implementing the DomainTracker port."""

    domain: ClassVar[str] = "energy"

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always, until Phase 6 lands.
        """
        raise NotImplementedError("energy tracker is a Phase 6 roadmap item")
