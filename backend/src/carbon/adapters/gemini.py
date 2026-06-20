# SPDX-License-Identifier: MIT
"""Vertex AI Gemini client behind a mockable port.

The :class:`GeminiClient` Protocol is the seam the application layer depends on;
unit tests substitute a fake. :class:`VertexGeminiClient` is the real adapter
with an explicit per-request timeout, bounded concurrency, bounded retries with
exponential backoff, and a capped output-token budget — the abuse/cost controls
required by the plan.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

import vertexai
from google.api_core.exceptions import GoogleAPIError
from vertexai.generative_models import GenerationConfig, GenerativeModel

from carbon.core.config import Settings

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 8.0
DEFAULT_MAX_CONCURRENCY = 8
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_S = 0.25
DEFAULT_MAX_OUTPUT_TOKENS = 512

_RETRYABLE: tuple[type[Exception], ...] = (TimeoutError, GoogleAPIError, ValueError)


class GeminiError(RuntimeError):
    """Raised when the LLM call fails after exhausting retries."""


class GeminiClient(Protocol):
    """Port for an LLM that returns a raw JSON phrasing string."""

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return the model's raw text response for the given prompts."""
        ...


class VertexGeminiClient:
    """Vertex AI Gemini adapter implementing :class:`GeminiClient`.

    The Vertex SDK is synchronous, so each call runs in a worker thread wrapped
    by :func:`asyncio.wait_for` to enforce a hard per-request timeout.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_s: float = DEFAULT_BACKOFF_S,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> None:
        """Configure the client. Network calls happen only in :meth:`generate`."""
        self._settings = settings
        self._timeout_s = timeout_s
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._max_retries = max_retries
        self._backoff_s = backoff_s
        self._max_output_tokens = max_output_tokens
        self._model: GenerativeModel | None = None

    def _get_model(self) -> GenerativeModel:
        """Lazily build the Vertex generative model on first use."""
        if self._model is None:
            vertexai.init(
                project=self._settings.gcp_project_id,
                location=self._settings.vertex_region,
            )
            self._model = GenerativeModel(self._settings.gemini_model_id)
        return self._model

    def _call_sync(self, system_prompt: str, user_prompt: str) -> str:
        """Blocking Vertex call executed in a worker thread."""
        model = self._get_model()
        prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                max_output_tokens=self._max_output_tokens,
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
        return str(response.text)

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini with bounded concurrency, timeout, and retries.

        Raises:
            GeminiError: If all attempts fail or time out.
        """
        last_exc: Exception | None = None
        async with self._semaphore:
            for attempt in range(self._max_retries + 1):
                try:
                    return await asyncio.wait_for(
                        asyncio.to_thread(self._call_sync, system_prompt, user_prompt),
                        timeout=self._timeout_s,
                    )
                except _RETRYABLE as exc:
                    last_exc = exc
                    _LOGGER.warning(
                        "gemini_call_failed",
                        extra={
                            "attempt": attempt,
                            "error_type": type(exc).__name__,
                        },
                    )
                    if attempt >= self._max_retries:
                        break
                    await asyncio.sleep(self._backoff_s * (2**attempt))
        raise GeminiError("gemini generation failed") from last_exc
