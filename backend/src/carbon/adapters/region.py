# SPDX-License-Identifier: MIT
"""Region resolution from a trusted load-balancer geo header.

The leaderboard is keyed by coarse region (country) so users compete locally
without exposing precise location. Region is read from a geo header the
front-door load balancer injects (for example ``X-Client-Geo-Country``) rather
than from a bundled, licensed GeoIP database — keeping the repo lean and avoiding
any copyleft data. The :class:`RegionResolver` Protocol lets tests inject a fake
without HTTP.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Protocol

DEFAULT_GEO_HEADER = "x-client-geo-country"
GLOBAL_REGION = "global"

# ISO 3166-1 alpha-2 country codes are two ASCII letters; anything else is
# treated as unknown and collapsed to the global region.
_COUNTRY_RE = re.compile(r"^[A-Za-z]{2}$")


class RegionResolver(Protocol):
    """Port that maps request headers to a coarse region key."""

    def resolve(self, headers: Mapping[str, str]) -> str:
        """Return the region key for a request (``global`` when unknown)."""
        ...


class HeaderRegionResolver:
    """Resolves region from a configured geo header, defaulting to global."""

    def __init__(self, *, header: str = DEFAULT_GEO_HEADER) -> None:
        """Initialise with the header name the load balancer populates."""
        self._header = header.lower()

    def resolve(self, headers: Mapping[str, str]) -> str:
        """Return the upper-cased country code, or ``global`` if absent/invalid.

        Args:
            headers: Case-insensitive request headers (Starlette ``Headers``).

        Returns:
            A normalised region key safe to use as a leaderboard board suffix.
        """
        raw = headers.get(self._header)
        if raw is None:
            return GLOBAL_REGION
        candidate = raw.strip()
        if not _COUNTRY_RE.match(candidate):
            return GLOBAL_REGION
        return candidate.upper()
