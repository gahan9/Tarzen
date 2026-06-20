# SPDX-License-Identifier: MIT
"""Golden-table and validation tests for the energy tracker."""

from __future__ import annotations

import pytest

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.trackers.energy import EnergyTracker

# factor(electricity)=0.2071/kWh; natural_gas=0.18293/kWh. Expected = factor * kwh
# rounded to 4 dp.
_GOLDEN = [
    ("electricity", 100.0, 20.71),
    ("electricity", 0.0, 0.0),
    ("natural_gas", 250.0, 45.7325),
    ("natural_gas", 1.0, 0.1829),
]


@pytest.mark.parametrize(("mode", "kwh", "expected"), _GOLDEN)
def test_energy_compute_matches_golden_table(
    mode: str, kwh: float, expected: float
) -> None:
    """Computed kg CO2e matches the deterministic golden table."""
    result = EnergyTracker().compute({"mode": mode, "kwh": kwh})
    assert result.kg_co2e == pytest.approx(expected)
    assert result.domain == "energy"
    assert sum(item.kg_co2e for item in result.breakdown) == pytest.approx(expected)


def test_energy_unknown_mode_raises() -> None:
    """An unregistered mode raises UnsupportedModeError."""
    with pytest.raises(UnsupportedModeError):
        EnergyTracker().compute({"mode": "nuclear", "kwh": 10.0})


def test_energy_missing_quantity_raises() -> None:
    """A missing kwh value raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        EnergyTracker().compute({"mode": "electricity"})


def test_energy_negative_quantity_raises() -> None:
    """A negative kwh value raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        EnergyTracker().compute({"mode": "electricity", "kwh": -1.0})
