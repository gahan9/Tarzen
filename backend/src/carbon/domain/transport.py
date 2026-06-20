# SPDX-License-Identifier: MIT
"""Rule-based transport footprint calculator.

Pure and deterministic: given a mode, distance, and passenger count it returns
a :class:`~carbon.domain.models.FootprintResult` using versioned emission
factors. No I/O occurs at call time — factors are loaded once and cached by
:mod:`carbon.domain.factors`.
"""

from __future__ import annotations

from typing import ClassVar

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.factors import FactorCatalogue, get_factor_catalogue
from carbon.domain.models import BreakdownItem, FootprintResult

_ROUNDING = 4


class TransportTracker:
    """Deterministic transport emissions calculator.

    Implements the :class:`~carbon.domain.ports.DomainTracker` port.
    """

    domain: ClassVar[str] = "transport"

    def __init__(self, catalogue: FactorCatalogue | None = None) -> None:
        """Initialise the tracker.

        Args:
            catalogue: Optional explicit factor catalogue, primarily for tests.
                Defaults to the process-wide cached catalogue.
        """
        self._catalogue = catalogue or get_factor_catalogue()

    def compute(self, params: object) -> FootprintResult:
        """Compute a transport footprint.

        Args:
            params: Mapping with ``mode`` (str), ``distance_km`` (number), and
                optional ``passengers`` (int, defaults to 1).

        Returns:
            The personal footprint share for the activity.

        Raises:
            InvalidInputError: If required parameters are missing or malformed.
            UnsupportedModeError: If ``mode`` has no registered factor.
        """
        if not isinstance(params, dict):
            raise InvalidInputError("transport parameters must be a mapping")

        mode = params.get("mode")
        distance = params.get("distance_km")
        passengers = params.get("passengers", 1)

        if not isinstance(mode, str):
            raise InvalidInputError("'mode' is required")
        if not isinstance(distance, (int, float)) or isinstance(distance, bool):
            raise InvalidInputError("'distance_km' must be a number")
        if not isinstance(passengers, int) or isinstance(passengers, bool):
            raise InvalidInputError("'passengers' must be an integer")
        if distance < 0:
            raise InvalidInputError("'distance_km' must be non-negative")
        if passengers < 1:
            raise InvalidInputError("'passengers' must be at least 1")

        factor = self._catalogue.factor_for(self.domain, mode)
        if factor is None:
            raise UnsupportedModeError(f"unsupported transport mode: {mode}")

        raw = factor.factor * float(distance)
        personal = raw / passengers if factor.shared_by_passengers else raw
        personal = round(personal, _ROUNDING)

        label = f"{factor.label} ({distance:g} km)"
        return FootprintResult(
            domain=self.domain,
            kg_co2e=personal,
            breakdown=(BreakdownItem(label=label, kg_co2e=personal),),
        )
