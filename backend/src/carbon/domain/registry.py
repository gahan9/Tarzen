# SPDX-License-Identifier: MIT
"""Tracker registry mapping a domain name to its :class:`DomainTracker`.

Adding a new domain means implementing a tracker and registering it here — no
changes to the API or application layers are required.
"""

from __future__ import annotations

from carbon.domain.errors import UnsupportedDomainError
from carbon.domain.ports import DomainTracker
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
    """Build the registry of trackers active in the MVP.

    Roadmap trackers (energy/food/shopping/waste) exist as stubs but are not
    registered until implemented, so requests for them fail cleanly.
    """
    return TrackerRegistry({TransportTracker.domain: TransportTracker()})
