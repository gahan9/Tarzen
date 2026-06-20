# SPDX-License-Identifier: MIT
"""Tests for the relatable benchmark cross-reference logic."""

from __future__ import annotations

import pytest

from carbon.domain.benchmarks import cross_reference


def test_cross_reference_non_positive_returns_none() -> None:
    """Non-positive figures have no benchmark."""
    assert cross_reference(0.0) is None
    assert cross_reference(-5.0) is None


def test_cross_reference_large_figure_uses_household_scale() -> None:
    """A large figure maps to the household-electricity benchmark."""
    match = cross_reference(500.0)
    assert match is not None
    assert match.benchmark.key == "household_electricity_month"
    assert match.count == pytest.approx(2.0)


def test_cross_reference_small_figure_uses_small_scale() -> None:
    """A tiny figure maps to a small-magnitude benchmark, not household scale."""
    match = cross_reference(0.02)
    assert match is not None
    assert match.benchmark.key in {"smartphone_charge", "km_by_car"}
    assert "about" in match.sentence
