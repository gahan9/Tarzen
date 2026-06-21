# SPDX-License-Identifier: MIT
"""Tests for header-based region resolution."""

from __future__ import annotations

from carbon.adapters.region import GLOBAL_REGION, HeaderRegionResolver


def test_valid_country_code_is_upper_cased() -> None:
    """A valid two-letter code is normalised to upper case."""
    resolver = HeaderRegionResolver()

    assert resolver.resolve({"x-client-geo-country": "gb"}) == "GB"


def test_missing_header_is_global() -> None:
    """An absent geo header collapses to the global region."""
    resolver = HeaderRegionResolver()

    assert resolver.resolve({}) == GLOBAL_REGION


def test_invalid_value_is_global() -> None:
    """A non-ISO value (e.g. a city name) collapses to the global region."""
    resolver = HeaderRegionResolver()

    assert resolver.resolve({"x-client-geo-country": "London"}) == GLOBAL_REGION
