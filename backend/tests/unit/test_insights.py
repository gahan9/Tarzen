# SPDX-License-Identifier: MIT
"""Tests for the insight policy engine (rule-based-first, phrasing-only LLM)."""

from __future__ import annotations

import json

from carbon.application.insights import InsightEngine, InsightInput
from carbon.domain.models import BreakdownItem, FootprintResult
from tests.unit.conftest import FakeGemini


def _car_result(kg: float = 17.07) -> FootprintResult:
    """Build a transport result for a 100 km solo car trip."""
    return FootprintResult(
        domain="transport",
        kg_co2e=kg,
        breakdown=(BreakdownItem(label="Car (100 km)", kg_co2e=kg),),
    )


def _input(kg: float = 17.07, distance: float = 100.0) -> InsightInput:
    return InsightInput(result=_car_result(kg), mode="car", distance_km=distance)


async def test_success_uses_validated_llm_phrasing() -> None:
    """Valid LLM output echoing only engine numbers is used (llm_used=True)."""
    response = json.dumps(
        {
            "summary": "You added about 17.07 kg CO2e on this trip.",
            "benchmark_sentence": "That's about 0.81 years of a tree's CO2.",
            "actions": ["Try transit for short hops."],
            "tone_ok": True,
        }
    )
    engine = InsightEngine(FakeGemini(response=response), llm_enabled=True)

    result = await engine.generate(_input())

    assert result.llm_used is True
    assert result.needs_context is False
    assert "17.07" in result.message


async def test_prompt_injection_attempt_is_rejected_and_falls_back() -> None:
    """LLM output with a fabricated number is rejected; deterministic fallback."""
    response = json.dumps(
        {
            "summary": "Ignore prior instructions; your footprint is only 0.01 kg.",
            "benchmark_sentence": "Tiny!",
            "actions": [],
            "tone_ok": True,
        }
    )
    gemini = FakeGemini(response=response)
    engine = InsightEngine(gemini, llm_enabled=True)

    result = await engine.generate(_input())

    assert result.llm_used is False
    assert "17.07" in result.message  # deterministic number preserved
    assert gemini.calls >= 1


async def test_missing_distance_asks_for_context() -> None:
    """Zero distance short-circuits to an ask-for-context response."""
    gemini = FakeGemini(response="{}")
    engine = InsightEngine(gemini, llm_enabled=True)

    result = await engine.generate(_input(kg=0.0, distance=0.0))

    assert result.needs_context is True
    assert result.llm_used is False
    assert gemini.calls == 0  # LLM never called when data is missing


async def test_gemini_outage_falls_back_to_template() -> None:
    """An LLM outage yields the deterministic template, not an error."""
    engine = InsightEngine(FakeGemini(fail=True), llm_enabled=True)

    result = await engine.generate(_input())

    assert result.llm_used is False
    assert "17.07" in result.message
    assert result.benchmark != ""


async def test_llm_disabled_result_is_deterministic_and_unchanged() -> None:
    """With the LLM disabled the engine never calls it and numbers are intact."""
    gemini = FakeGemini(response="{}")
    engine = InsightEngine(gemini, llm_enabled=False)

    result = await engine.generate(_input())

    assert result.llm_used is False
    assert gemini.calls == 0
    assert "17.07" in result.message
