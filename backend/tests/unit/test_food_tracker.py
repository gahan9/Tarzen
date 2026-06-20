# SPDX-License-Identifier: MIT
"""Golden-table and validation tests for the food tracker."""

from __future__ import annotations

import pytest

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.trackers.food import FoodTracker

# Per-meal factors (kg CO2e): beef=6.0, pork=1.7, chicken=1.2, fish=1.3,
# vegetarian=0.5, vegan=0.4. Expected = factor * servings.
_GOLDEN = [
    ("beef_meal", 1, 6.0),
    ("beef_meal", 3, 18.0),
    ("chicken_meal", 2, 2.4),
    ("vegetarian_meal", 4, 2.0),
    ("vegan_meal", 0, 0.0),
]


@pytest.mark.parametrize(("mode", "servings", "expected"), _GOLDEN)
def test_food_compute_matches_golden_table(
    mode: str, servings: int, expected: float
) -> None:
    """Computed kg CO2e matches the deterministic golden table."""
    result = FoodTracker().compute({"mode": mode, "servings": servings})
    assert result.kg_co2e == pytest.approx(expected)
    assert result.domain == "food"
    assert sum(item.kg_co2e for item in result.breakdown) == pytest.approx(expected)


def test_food_unknown_mode_raises() -> None:
    """An unregistered meal category raises UnsupportedModeError."""
    with pytest.raises(UnsupportedModeError):
        FoodTracker().compute({"mode": "insect_meal", "servings": 1})


def test_food_non_integer_servings_raises() -> None:
    """A non-integer servings value raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        FoodTracker().compute({"mode": "beef_meal", "servings": 1.5})


def test_food_missing_servings_raises() -> None:
    """A missing servings value raises InvalidInputError."""
    with pytest.raises(InvalidInputError):
        FoodTracker().compute({"mode": "beef_meal"})
