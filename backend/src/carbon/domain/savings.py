# SPDX-License-Identifier: MIT
"""Rule-based carbon-savings calculator (avoided emissions).

Savings are *avoided* emissions relative to driving the same distance solo in an
average car — the deterministic complement of the emitting trackers. The
calculation is pure and reuses the versioned transport factors loaded once by
:mod:`carbon.domain.factors`; no I/O occurs at call time.

Two modes are supported:

* **Carpool** (``mode == "car"``): sharing one car across ``passengers`` people
  avoids the per-passenger share that solo driving would have emitted::

      saved = car_factor * distance * (1 - 1 / passengers)

  A single occupant saves nothing (it *is* the baseline).
* **Transit** (``mode in {"bus", "rail"}``): replacing a solo car trip with a
  lower-carbon mode avoids the difference between the two factors::

      saved = (car_factor - transit_factor) * distance

Savings are clamped at ``>= 0`` so a (hypothetical) higher-carbon alternative can
never present as a "saving".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.factors import FactorCatalogue, get_factor_catalogue
from carbon.domain.models import BreakdownItem

_ROUNDING = 4
_TRANSPORT_DOMAIN = "transport"
# The solo-car baseline uses the transport ``car`` factor; ``carpool`` shares
# that same car across occupants.
_BASELINE_FACTOR_MODE = "car"
_CARPOOL_MODE = "carpool"


@dataclass(frozen=True, slots=True)
class SavingsResult:
    """The deterministic result of a carbon-savings calculation.

    Attributes:
        mode: The lower-carbon mode that replaced solo driving.
        baseline_kg_co2e: Emissions of driving the distance solo in a car.
        actual_kg_co2e: Emissions actually incurred by the chosen mode.
        kg_co2e_saved: Avoided emissions (``baseline - actual``, clamped >= 0).
        breakdown: Ordered per-component contributions explaining the saving.
    """

    mode: str
    baseline_kg_co2e: float
    actual_kg_co2e: float
    kg_co2e_saved: float
    breakdown: tuple[BreakdownItem, ...]


class SavingsCalculator:
    """Deterministic avoided-emissions calculator.

    Pure: identical inputs always yield identical results. Factors are loaded
    once and cached, so no file or network I/O happens per call.
    """

    domain: ClassVar[str] = "savings"

    def __init__(self, catalogue: FactorCatalogue | None = None) -> None:
        """Initialise the calculator.

        Args:
            catalogue: Optional explicit factor catalogue, primarily for tests.
                Defaults to the process-wide cached catalogue.
        """
        self._catalogue = catalogue or get_factor_catalogue()

    def compute(
        self, *, mode: str, distance_km: float, passengers: int = 1
    ) -> SavingsResult:
        """Compute avoided emissions for a single trip.

        Args:
            mode: ``carpool`` for sharing a car, or a transit mode
                (``bus``/``rail``) that replaced a solo car trip.
            distance_km: Trip distance in kilometres (non-negative).
            passengers: Vehicle occupancy for carpooling (defaults to 1).

        Returns:
            The deterministic :class:`SavingsResult`.

        Raises:
            InvalidInputError: If inputs are structurally invalid.
            UnsupportedModeError: If ``mode`` has no registered transport factor.
        """
        if not isinstance(mode, str):
            raise InvalidInputError("'mode' is required")
        if not isinstance(distance_km, (int, float)) or isinstance(distance_km, bool):
            raise InvalidInputError("'distance_km' must be a number")
        if not isinstance(passengers, int) or isinstance(passengers, bool):
            raise InvalidInputError("'passengers' must be an integer")
        if distance_km < 0:
            raise InvalidInputError("'distance_km' must be non-negative")
        if passengers < 1:
            raise InvalidInputError("'passengers' must be at least 1")

        baseline_factor = self._catalogue.factor_for(
            _TRANSPORT_DOMAIN, _BASELINE_FACTOR_MODE
        )
        if baseline_factor is None:  # pragma: no cover - catalogue always has car
            raise UnsupportedModeError("baseline car factor is unavailable")
        baseline = baseline_factor.factor * float(distance_km)

        if mode == _CARPOOL_MODE:
            actual = baseline / passengers
            label = f"Carpool of {passengers} ({distance_km:g} km)"
        else:
            factor = self._catalogue.factor_for(_TRANSPORT_DOMAIN, mode)
            if factor is None:
                raise UnsupportedModeError(f"unsupported savings mode: {mode}")
            actual = factor.factor * float(distance_km)
            label = f"{factor.label} instead of car ({distance_km:g} km)"

        saved = max(baseline - actual, 0.0)
        return SavingsResult(
            mode=mode,
            baseline_kg_co2e=round(baseline, _ROUNDING),
            actual_kg_co2e=round(actual, _ROUNDING),
            kg_co2e_saved=round(saved, _ROUNDING),
            breakdown=(BreakdownItem(label=label, kg_co2e=round(saved, _ROUNDING)),),
        )
