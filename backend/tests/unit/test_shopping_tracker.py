# SPDX-License-Identifier: MIT
"""Golden-table and validation tests for the shopping tracker."""

from __future__ import annotations

import pytest

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.trackers.shopping import ShoppingTracker

# Spend factors (kg CO2e per GBP): clothing=0.5, electronics=0.3, furniture=0.45,
# general_goods=0.4. Expected = factor * spend rounded to 4 dp.
_GOLDEN = [
    ("clothing", 100.0, 50.0),
    ("electronics", 250.0, 75.0),
    ("furniture", 40.0, 18.0),
    ("general_goods", 12.5, 5.0),
    ("clothing", 0.0, 0.0),
]


@pytest.mark.parametrize(("mode", "spend", "expected"), _GOLDEN)
def test_shopping_compute_matches_golden_table(
    mode: str, spend: float, expected: float
) -> None:
    """Computed kg CO2e matches the deterministic golden table."""
    result = ShoppingTracker().compute({"mode": mode, "spend": spend})
    assert result.kg_co2e == pytest.approx(expected)
    assert result.domain == "shopping"
    assert sum(item.kg_co2e for item in result.breakdown) == pytest.approx(expected)


def test_shopping_unknown_mode_raises() -> None:
    """An unregistered category raises UnsupportedModeError."""
    with pytest.raises(UnsupportedModeError):
        ShoppingTracker().compute({"mode": "jewellery", "spend": 10.0})


def test_shopping_negative_spend_raises() -> None:
    """A negative spend value raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        ShoppingTracker().compute({"mode": "clothing", "spend": -5.0})


def test_shopping_missing_spend_raises() -> None:
    """A missing spend value raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        ShoppingTracker().compute({"mode": "clothing"})
