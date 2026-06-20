# SPDX-License-Identifier: MIT
"""Golden-table and validation tests for the transport tracker."""

from __future__ import annotations

import pytest

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.transport import TransportTracker

# factor(car)=0.1707 (vehicle_km, shared); bus=0.10227; rail=0.03549;
# flight=0.15102 (passenger_km, not shared). Expected = factor * km / passengers
# for car; factor * km otherwise. Values rounded to 4 dp.
_GOLDEN = [
    ("car", 100.0, 1, 17.07),
    ("car", 100.0, 2, 8.535),
    ("car", 0.0, 1, 0.0),
    ("bus", 50.0, 1, 5.1135),
    ("rail", 200.0, 1, 7.098),
    ("flight", 1000.0, 1, 151.02),
    ("flight", 1000.0, 3, 151.02),  # passengers do not divide a per-pax factor
]


@pytest.mark.parametrize(("mode", "distance", "passengers", "expected"), _GOLDEN)
def test_transport_compute_matches_golden_table(
    mode: str, distance: float, passengers: int, expected: float
) -> None:
    """Computed kg CO2e matches the deterministic golden table."""
    tracker = TransportTracker()
    result = tracker.compute(
        {"mode": mode, "distance_km": distance, "passengers": passengers}
    )
    assert result.kg_co2e == pytest.approx(expected)
    assert result.domain == "transport"
    assert sum(item.kg_co2e for item in result.breakdown) == pytest.approx(expected)


def test_transport_unknown_mode_raises() -> None:
    """An unregistered mode raises UnsupportedModeError."""
    tracker = TransportTracker()
    with pytest.raises(UnsupportedModeError):
        tracker.compute({"mode": "teleport", "distance_km": 10.0, "passengers": 1})


def test_transport_negative_distance_raises() -> None:
    """A negative distance raises InvalidInputError."""
    tracker = TransportTracker()
    with pytest.raises(InvalidInputError):
        tracker.compute({"mode": "car", "distance_km": -1.0, "passengers": 1})


def test_transport_zero_passengers_raises() -> None:
    """A passenger count below one raises InvalidInputError."""
    tracker = TransportTracker()
    with pytest.raises(InvalidInputError):
        tracker.compute({"mode": "car", "distance_km": 10.0, "passengers": 0})
