# SPDX-License-Identifier: MIT
"""Tracker registry mapping a domain name to its :class:`DomainTracker`.

Adding a new domain means implementing a tracker and registering it here — no
changes to the API or application layers are required.
"""

from __future__ import annotations

from carbon.domain.errors import UnsupportedDomainError
from carbon.domain.ports import DomainTracker
from carbon.domain.trackers.energy import EnergyTracker
from carbon.domain.trackers.food import FoodTracker
from carbon.domain.trackers.shopping import ShoppingTracker
from carbon.domain.trackers.waste import WasteTracker
from carbon.domain.transport import TransportTracker


class TrackerRegistry:
    """An immutable lookup of active domain trackers."""

    def __init__(self, trackers: dict[str, DomainTracker]) -> None:
        """Initialise with a mapping of domain name to tracker."""
        self._trackers = dict(trackers)

    def get(self, domain: str) -> DomainTracker:
        """Return the tracker for ``domain``.

        Raises:
            UnsupportedDomainError: If no tracker is registered for ``domain``.
        """
        tracker = self._trackers.get(domain)
        if tracker is None:
            raise UnsupportedDomainError(f"no tracker for domain: {domain}")
        return tracker

    def domains(self) -> tuple[str, ...]:
        """Return the registered domain names."""
        return tuple(self._trackers)


def build_default_registry() -> TrackerRegistry:
    """Build the registry of active domain trackers.

    Adding a domain means implementing a :class:`DomainTracker` and listing it
    here — the API, schema-routing, and application layers need no other edits.
    """
    trackers: tuple[DomainTracker, ...] = (
        TransportTracker(),
        EnergyTracker(),
        FoodTracker(),
        ShoppingTracker(),
        WasteTracker(),
    )
    return TrackerRegistry({tracker.domain: tracker for tracker in trackers})
