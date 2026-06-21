# SPDX-License-Identifier: MIT
"""Golden-table tests for the deterministic savings calculator.

Values are derived from the public factor catalogue (car=0.1707, bus=0.10227,
rail=0.03549 kg CO2e/km) against a solo-car baseline, so any drift in the math
or the factors is caught here.
"""

from __future__ import annotations

import pytest

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.registry import build_savings_calculator


@pytest.mark.parametrize(
    ("mode", "distance_km", "passengers", "expected"),
    [
        ("carpool", 30.0, 3, 3.414),  # 5.121 baseline - 1.707 actual
        ("carpool", 10.0, 2, 0.8535),  # 1.707 - 0.8535
        ("carpool", 10.0, 1, 0.0),  # solo carpool saves nothing
        ("bus", 20.0, 1, 1.3686),  # 3.414 - 2.0454
        ("rail", 50.0, 1, 6.7605),  # 8.535 - 1.7745
    ],
)
def test_savings_golden_table(
    mode: str, distance_km: float, passengers: int, expected: float
) -> None:
    """Each mode yields the exact avoided-emissions figure."""
    calc = build_savings_calculator()

    result = calc.compute(mode=mode, distance_km=distance_km, passengers=passengers)

    assert result.kg_co2e_saved == expected
    assert result.kg_co2e_saved >= 0.0
    assert result.breakdown[0].kg_co2e == expected


def test_carpool_baseline_matches_solo_car() -> None:
    """A carpool's baseline equals a solo-car trip over the same distance."""
    calc = build_savings_calculator()

    result = calc.compute(mode="carpool", distance_km=100.0, passengers=4)

    assert result.baseline_kg_co2e == 17.07  # 0.1707 * 100
    assert result.actual_kg_co2e == 4.2675  # baseline / 4


def test_zero_distance_saves_nothing() -> None:
    """A zero-distance trip is valid and saves nothing."""
    calc = build_savings_calculator()

    assert calc.compute(mode="rail", distance_km=0.0).kg_co2e_saved == 0.0


def test_negative_distance_rejected() -> None:
    """A negative distance is a structural input error."""
    calc = build_savings_calculator()

    with pytest.raises(InvalidInputError):
        calc.compute(mode="carpool", distance_km=-1.0, passengers=2)


def test_unsupported_mode_rejected() -> None:
    """A transit mode with no registered factor is rejected."""
    calc = build_savings_calculator()

    with pytest.raises(UnsupportedModeError):
        calc.compute(mode="teleport", distance_km=5.0)
