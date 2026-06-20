# SPDX-License-Identifier: MIT
"""Structured-output schema for the LLM phrasing step.

The Gemini client returns JSON validated against :class:`GeminiPhrasing`. The
LLM only rephrases pre-computed copy; every number is injected by the engine and
re-verified after generation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GeminiPhrasing(BaseModel):
    """Validated phrasing returned by the LLM (no numeric authority)."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=400)
    benchmark_sentence: str = Field(min_length=1, max_length=400)
    actions: list[str] = Field(default_factory=list, max_length=3)
    tone_ok: bool = True
