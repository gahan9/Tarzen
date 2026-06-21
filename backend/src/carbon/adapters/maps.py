# SPDX-License-Identifier: MIT
"""Google Maps Distance Matrix adapter behind a mockable port.

Verified tickets give an origin and destination but not a distance; the
:class:`DistanceProvider` port resolves the road distance so the savings domain
can compute avoided emissions. The real adapter calls the Distance Matrix API
over HTTPS with an explicit timeout and an API key held as a
:class:`~pydantic.SecretStr` (unwrapped only at the request boundary). Unit tests
inject a fake, so no live call or key is needed in CI.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx
from pydantic import SecretStr

_LOGGER = logging.getLogger(__name__)

_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
DEFAULT_TIMEOUT_S = 8.0
_METRES_PER_KM = 1000.0


class DistanceError(RuntimeError):
    """Raised when a distance lookup fails or returns no usable route."""


class DistanceProvider(Protocol):
    """Port that resolves the distance between two places, in kilometres."""

    async def distance_km(self, origin: str, destination: str) -> float:
        """Return the road distance in kilometres between two place strings."""
        ...


class GoogleMapsDistanceProvider:
    """Distance Matrix-backed :class:`DistanceProvider`."""

    def __init__(
        self,
        api_key: SecretStr,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialise with the API key and an optional shared HTTP client.

        Args:
            api_key: The Maps API key, kept secret until the request boundary.
            timeout_s: Hard per-request timeout.
            client: Optional injected ``httpx.AsyncClient`` (reused if given).
        """
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._client = client

    async def distance_km(self, origin: str, destination: str) -> float:
        """Resolve the driving distance between two places.

        Raises:
            DistanceError: On a transport error, non-OK API status, or a route
                that the API could not resolve.
        """
        params = {
            "origins": origin,
            "destinations": destination,
            "units": "metric",
            "key": self._api_key.get_secret_value(),
        }
        try:
            payload = await self._fetch(params)
        except httpx.HTTPError as exc:
            _LOGGER.warning("maps_distance_transport_error")
            raise DistanceError("distance lookup transport error") from exc
        return self._parse_distance(payload)

    async def _fetch(self, params: dict[str, str]) -> dict[str, object]:
        """Perform the HTTP GET, reusing the injected client when present."""
        if self._client is not None:
            response = await self._client.get(
                _DISTANCE_MATRIX_URL, params=params, timeout=self._timeout_s
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            return data
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.get(_DISTANCE_MATRIX_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return data

    @staticmethod
    def _parse_distance(payload: dict[str, object]) -> float:
        """Extract metres from a Distance Matrix payload and convert to km.

        Raises:
            DistanceError: If the payload is not a resolved single-route result.
        """
        if payload.get("status") != "OK":
            raise DistanceError("distance matrix returned a non-OK status")
        rows = payload.get("rows")
        if not isinstance(rows, list) or not rows:
            raise DistanceError("distance matrix returned no rows")
        elements = rows[0].get("elements") if isinstance(rows[0], dict) else None
        if not isinstance(elements, list) or not elements:
            raise DistanceError("distance matrix returned no elements")
        element = elements[0]
        if not isinstance(element, dict) or element.get("status") != "OK":
            raise DistanceError("distance matrix could not resolve the route")
        distance = element.get("distance")
        if not isinstance(distance, dict) or "value" not in distance:
            raise DistanceError("distance matrix element has no distance value")
        return float(distance["value"]) / _METRES_PER_KM
