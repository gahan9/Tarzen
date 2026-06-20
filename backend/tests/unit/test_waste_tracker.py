# SPDX-License-Identifier: MIT
"""Golden-table and validation tests for the waste tracker."""

from __future__ import annotations

import pytest

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.trackers.waste import WasteTracker

# Waste factors (kg CO2e per kg): landfill=0.4467, recycling=0.0211,
# composting=0.0089. Expected = factor * waste_kg rounded to 4 dp.
_GOLDEN = [
    ("landfill", 10.0, 4.467),
    ("recycling", 10.0, 0.211),
    ("composting", 100.0, 0.89),
    ("landfill", 0.0, 0.0),
]


@pytest.mark.parametrize(("mode", "waste_kg", "expected"), _GOLDEN)
def test_waste_compute_matches_golden_table(
    mode: str, waste_kg: float, expected: float
) -> None:
    """Computed kg CO2e matches the deterministic golden table."""
    result = WasteTracker().compute({"mode": mode, "waste_kg": waste_kg})
    assert result.kg_co2e == pytest.approx(expected)
    assert result.domain == "waste"
    assert sum(item.kg_co2e for item in result.breakdown) == pytest.approx(expected)


def test_waste_unknown_mode_raises() -> None:
    """An unregistered waste stream raises UnsupportedModeError."""
    with pytest.raises(UnsupportedModeError):
        WasteTracker().compute({"mode": "incineration", "waste_kg": 1.0})


def test_waste_negative_mass_raises() -> None:
    """A negative mass raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        WasteTracker().compute({"mode": "landfill", "waste_kg": -1.0})


def test_waste_missing_mass_raises() -> None:
    """A missing mass raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        WasteTracker().compute({"mode": "landfill"})
