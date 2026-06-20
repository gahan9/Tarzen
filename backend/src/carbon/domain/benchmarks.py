# SPDX-License-Identifier: MIT
"""Relatable benchmark catalogue and deterministic cross-reference logic.

Maps an emission figure (kg CO2e) to a familiar, same-order-of-magnitude
equivalent (e.g. "about 0.6 months of household electricity"). All magnitudes
come from this versioned catalogue; the LLM never invents these numbers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Benchmark:
    """A relatable equivalence used to contextualise an emission figure.

    Attributes:
        key: Stable identifier for the benchmark.
        unit_kg_co2e: Emissions represented by one unit of this benchmark.
        singular: Noun phrase for a single unit (e.g. "month of household
            electricity").
        plural: Noun phrase for multiple units.
    """

    key: str
    unit_kg_co2e: float
    singular: str
    plural: str


@dataclass(frozen=True, slots=True)
class BenchmarkMatch:
    """The chosen benchmark and the precomputed equivalence for a figure.

    Attributes:
        benchmark: The selected catalogue entry.
        count: How many benchmark units the figure equals (rounded for display).
        sentence: A ready-to-render deterministic sentence.
    """

    benchmark: Benchmark
    count: float
    sentence: str


# Public, order-of-magnitude reference values (kg CO2e). Sourced from public
# datasets (DEFRA/EPA/GHG Protocol); see docs/data-sources.md.
_CATALOGUE: tuple[Benchmark, ...] = (
    Benchmark(
        key="smartphone_charge",
        unit_kg_co2e=0.008,
        singular="smartphone charge",
        plural="smartphone charges",
    ),
    Benchmark(
        key="km_by_car",
        unit_kg_co2e=0.1707,
        singular="kilometre driven in an average car",
        plural="kilometres driven in an average car",
    ),
    Benchmark(
        key="vegetarian_meal",
        unit_kg_co2e=0.5,
        singular="vegetarian meal",
        plural="vegetarian meals",
    ),
    Benchmark(
        key="tree_year",
        unit_kg_co2e=21.0,
        singular="year of CO2 absorbed by a tree",
        plural="years of CO2 absorbed by a tree",
    ),
    Benchmark(
        key="household_electricity_month",
        unit_kg_co2e=250.0,
        singular="month of average household electricity",
        plural="months of average household electricity",
    ),
)


def _round_count(count: float) -> float:
    """Round a benchmark count to a friendly number of significant digits."""
    if count >= 100:
        return float(round(count))
    if count >= 10:
        return round(count, 1)
    return round(count, 2)


def cross_reference(kg_co2e: float) -> BenchmarkMatch | None:
    """Select the most relatable benchmark for an emission figure.

    Chooses the catalogue entry whose unit magnitude is closest to ``kg_co2e``
    on a log scale, preferring a count within a comfortable, intuitive range.

    Args:
        kg_co2e: The figure to contextualise, in kg CO2e.

    Returns:
        A :class:`BenchmarkMatch`, or ``None`` if the figure is non-positive.
    """
    if kg_co2e <= 0:
        return None

    best = min(
        _CATALOGUE,
        key=lambda b: abs(math.log10(kg_co2e / b.unit_kg_co2e)),
    )
    count = _round_count(kg_co2e / best.unit_kg_co2e)
    noun = best.singular if count == 1 else best.plural
    sentence = f"about {count:g} {noun}"
    return BenchmarkMatch(benchmark=best, count=count, sentence=sentence)


def catalogue() -> tuple[Benchmark, ...]:
    """Return the immutable benchmark catalogue."""
    return _CATALOGUE
