# SPDX-License-Identifier: MIT
"""Domain ports (Protocols) that decouple the core from concrete trackers.

A :class:`DomainTracker` turns a validated parameter mapping into a
:class:`~carbon.domain.models.FootprintResult`. New domains are added by
implementing this Protocol and registering the tracker — the API core needs
zero edits.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, Protocol, runtime_checkable

from carbon.domain.models import FootprintResult

TrackerParams = Mapping[str, object]


@runtime_checkable
class DomainTracker(Protocol):
    """Port for a deterministic, pure per-domain footprint calculator."""

    domain: ClassVar[str]

    def compute(self, params: TrackerParams) -> FootprintResult:
        """Compute a footprint result from validated parameters.

        Args:
            params: Validated, domain-specific parameters (already bounds-checked
                at the API boundary).

        Returns:
            The deterministic :class:`FootprintResult`.

        Raises:
            carbon.domain.errors.DomainError: If the parameters cannot be
                applied (e.g. unknown mode).
        """
        ...
