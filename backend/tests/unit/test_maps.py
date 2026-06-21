# SPDX-License-Identifier: MIT
"""Tests for the Google Maps Distance Matrix adapter (mocked transport)."""

from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from carbon.adapters.maps import DistanceError, GoogleMapsDistanceProvider


def _provider(handler: httpx.MockTransport) -> GoogleMapsDistanceProvider:
    client = httpx.AsyncClient(transport=handler)
    return GoogleMapsDistanceProvider(SecretStr("test-key"), client=client)


def _ok_payload(metres: int) -> dict[str, object]:
    return {
        "status": "OK",
        "rows": [
            {"elements": [{"status": "OK", "distance": {"value": metres}}]}
        ],
    }


async def test_distance_km_parses_metres() -> None:
    """A resolved route is converted from metres to kilometres."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["key"] == "test-key"
        return httpx.Response(200, json=_ok_payload(20_000))

    provider = _provider(httpx.MockTransport(handler))

    assert await provider.distance_km("A", "B") == 20.0


async def test_non_ok_top_status_raises() -> None:
    """A non-OK top-level status is a distance error."""
    provider = _provider(
        httpx.MockTransport(lambda r: httpx.Response(200, json={"status": "DENIED"}))
    )

    with pytest.raises(DistanceError):
        await provider.distance_km("A", "B")


async def test_unresolved_element_raises() -> None:
    """An element the API could not resolve is a distance error."""
    payload = {"status": "OK", "rows": [{"elements": [{"status": "ZERO_RESULTS"}]}]}
    provider = _provider(
        httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    )

    with pytest.raises(DistanceError):
        await provider.distance_km("A", "B")


async def test_transport_error_raises_distance_error() -> None:
    """An HTTP transport error is wrapped as a distance error."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    provider = _provider(httpx.MockTransport(handler))

    with pytest.raises(DistanceError):
        await provider.distance_km("A", "B")
