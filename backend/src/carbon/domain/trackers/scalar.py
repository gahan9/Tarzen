# SPDX-License-Identifier: MIT
"""Shared compute helper for single-quantity domain trackers.

Energy, food, shopping, and waste all share the same shape: a footprint is a
versioned emission factor multiplied by a single non-negative quantity (kWh,
meals, spend, or mass). This helper centralises that arithmetic and input
validation so each tracker stays a thin, declarative wrapper — and adding a new
single-quantity domain needs no edits to the API or application core.
"""

from __future__ import annotations

from collections.abc import Mapping

from carbon.domain.errors import InvalidInputError, UnsupportedModeError
from carbon.domain.factors import FactorCatalogue
from carbon.domain.models import BreakdownItem, FootprintResult

_ROUNDING = 4


def compute_scalar(
    *,
    domain: str,
    params: Mapping[str, object],
    quantity_key: str,
    unit: str,
    catalogue: FactorCatalogue,
    require_int: bool = False,
) -> FootprintResult:
    """Compute a footprint as ``factor * quantity`` for a single-quantity domain.

    Args:
        domain: Domain name used for factor lookup and the result tag.
        params: Validated parameter mapping; must contain ``mode`` and the
            quantity under ``quantity_key``.
        quantity_key: Mapping key holding the activity magnitude.
        unit: Human-readable unit appended to the breakdown label.
        catalogue: Emission-factor catalogue to resolve ``mode`` against.
        require_int: When ``True`` the quantity must be an ``int`` (e.g. meal
            servings); otherwise any non-negative number is accepted.

    Returns:
        The deterministic :class:`FootprintResult` for the activity.

    Raises:
        InvalidInputError: If parameters are missing or malformed.
        UnsupportedModeError: If ``mode`` has no registered factor.
    """
    if not isinstance(params, Mapping):
        raise InvalidInputError(f"{domain} parameters must be a mapping")

    mode = params.get("mode")
    quantity = params.get(quantity_key)

    if not isinstance(mode, str):
        raise InvalidInputError("'mode' is required")
    if require_int:
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise InvalidInputError(f"'{quantity_key}' must be an integer")
    elif not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
        raise InvalidInputError(f"'{quantity_key}' must be a number")
    if quantity < 0:
        raise InvalidInputError(f"'{quantity_key}' must be non-negative")

    factor = catalogue.factor_for(domain, mode)
    if factor is None:
        raise UnsupportedModeError(f"unsupported {domain} mode: {mode}")

    total = round(factor.factor * float(quantity), _ROUNDING)
    label = f"{factor.label} ({quantity:g} {unit})"
    return FootprintResult(
        domain=domain,
        kg_co2e=total,
        breakdown=(BreakdownItem(label=label, kg_co2e=total),),
    )
