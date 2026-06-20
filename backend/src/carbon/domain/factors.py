# SPDX-License-Identifier: MIT
"""Versioned emission-factor catalogue loaded once at module import.

The factor table is read from ``data/emission_factors.json`` a single time and
cached for the process lifetime via :func:`functools.lru_cache`. No per-request
file I/O occurs; callers receive an immutable view of the parsed data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Final

_DATA_PACKAGE: Final = "carbon.data"
_FACTORS_FILE: Final = "emission_factors.json"


@dataclass(frozen=True, slots=True)
class EmissionFactor:
    """A single emission factor and how it should be applied.

    Attributes:
        factor: Emissions per kilometre, in kg CO2e.
        basis: ``vehicle_km`` or ``passenger_km`` — describes what the factor
            measures.
        shared_by_passengers: When ``True`` the factor is for the whole vehicle
            and is divided across passengers to obtain a personal share.
        label: Human-readable mode label for breakdown rendering.
    """

    factor: float
    basis: str
    shared_by_passengers: bool
    label: str


@dataclass(frozen=True, slots=True)
class FactorCatalogue:
    """Immutable, versioned set of emission factors keyed by domain and mode.

    Attributes:
        version: Dataset version string for provenance and reproducibility.
        unit: The physical unit the factors are expressed in.
        source: Human-readable dataset citation.
        domains: Mapping of ``domain -> mode -> EmissionFactor``.
    """

    version: str
    unit: str
    source: str
    domains: dict[str, dict[str, EmissionFactor]]

    def factor_for(self, domain: str, mode: str) -> EmissionFactor | None:
        """Return the factor for ``domain``/``mode`` or ``None`` if absent."""
        return self.domains.get(domain, {}).get(mode)


@lru_cache(maxsize=1)
def get_factor_catalogue() -> FactorCatalogue:
    """Return the process-wide cached emission-factor catalogue.

    The JSON data file is parsed exactly once. Subsequent calls return the same
    cached, immutable catalogue.

    Returns:
        The parsed :class:`FactorCatalogue`.
    """
    raw_text = resources.files(_DATA_PACKAGE).joinpath(_FACTORS_FILE).read_text("utf-8")
    raw = json.loads(raw_text)
    domains: dict[str, dict[str, EmissionFactor]] = {}
    for domain, modes in raw["domains"].items():
        domains[domain] = {
            mode: EmissionFactor(
                factor=float(spec["factor"]),
                basis=str(spec["basis"]),
                shared_by_passengers=bool(spec["shared_by_passengers"]),
                label=str(spec["label"]),
            )
            for mode, spec in modes.items()
        }
    return FactorCatalogue(
        version=str(raw["version"]),
        unit=str(raw["unit"]),
        source=str(raw["source"]),
        domains=domains,
    )
