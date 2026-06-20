# SPDX-License-Identifier: MIT
"""Field-bounds and rejection tests for the wire schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from carbon.models.schemas import MAX_DISTANCE_KM, FootprintRequest


def test_valid_request_parses_with_default_passengers() -> None:
    """A minimal valid request defaults passengers to one."""
    req = FootprintRequest(domain="transport", mode="car", distance_km=42.0)
    assert req.passengers == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"domain": "transport", "mode": "car", "distance_km": -1.0},
        {"domain": "transport", "mode": "car", "distance_km": MAX_DISTANCE_KM + 1},
        {"domain": "transport", "mode": "car", "distance_km": 1.0, "passengers": 0},
        {"domain": "transport", "mode": "rocket", "distance_km": 1.0},
        {"domain": "", "mode": "car", "distance_km": 1.0},
        {"domain": "transport", "mode": "car", "distance_km": 1.0, "extra": 1},
    ],
)
def test_invalid_requests_are_rejected(payload: dict[str, object]) -> None:
    """Out-of-bounds, unknown-mode, empty-domain, and extra fields all reject."""
    with pytest.raises(ValidationError):
        FootprintRequest.model_validate(payload)
