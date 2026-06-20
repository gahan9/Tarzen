<!-- SPDX-License-Identifier: MIT -->

# Emission-factor data sources

All emission factors and benchmark magnitudes come from **public** datasets
under permissive/open terms. No GPL/AGPL/SSPL-licensed data is used. Each dataset
is recorded here with its license and version, and attributed in the root
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Active datasets (MVP)

| Dataset | Used for | Version | License / terms | Where |
|---------|----------|---------|-----------------|-------|
| **UK DEFRA / DESNZ — Greenhouse gas reporting: conversion factors 2024** | Transport emission factors (car, bus, rail, flight), kg CO₂e per km | `2024.1` | **Open Government Licence v3.0 (OGL v3.0)** — free reuse with attribution | `backend/src/carbon/data/emission_factors.json` (`source`/`version` fields) |

The factors in use (per `emission_factors.json`):

| Mode | Factor (kg CO₂e) | Basis | Shared by passengers |
|------|------------------|-------|----------------------|
| Car | 0.1707 / km | vehicle_km | yes (divided by passengers) |
| Bus | 0.10227 / km | passenger_km | no |
| Rail | 0.03549 / km | passenger_km | no |
| Flight | 0.15102 / km | passenger_km | no |

## Benchmark reference magnitudes

The relatable benchmark catalogue (`backend/src/carbon/domain/benchmarks.py`)
uses order-of-magnitude reference values for everyday equivalents (smartphone
charge, km driven, vegetarian meal, tree-year of CO₂, month of household
electricity). These are public, widely-published reference magnitudes and are
treated as the same OGL/public-domain class as the primary factors. The LLM
never invents these numbers; they live in the versioned catalogue.

## Datasets referenced for roadmap domains (Phases 6+)

These are named for the energy/food/shopping/waste trackers and are all
permissively licensed; factors will be added with explicit `version`/`source`
fields when those trackers are implemented.

| Dataset | Intended use | License / terms |
|---------|--------------|-----------------|
| **US EPA — Emission Factors for Greenhouse Gas Inventories** | Energy (grid intensity), waste factors | US Government work — public domain (no copyright) |
| **GHG Protocol — emission factor datasets / tools** | Cross-domain reference and methodology | Free use under GHG Protocol terms (attribution) |

## Compliance notes

- Attribution for OGL v3.0 and the above sources is provided in
  `THIRD_PARTY_NOTICES.md` and inline in `emission_factors.json`.
- Factors are versioned (`"version": "2024.1"`) so recalculations are
  reproducible and auditable; bumping a dataset is a data-file change, not a
  code change.
