# SPDX-License-Identifier: MIT
"""Tests for the Vertex vision client's retry/validation logic (no network).

The blocking model call (:meth:`VertexVisionClient._call_sync`) is replaced so
the retry, timeout-budget, and JSON-validation paths are exercised without
touching Vertex AI.
"""

from __future__ import annotations

import pytest

from carbon.adapters.vision import VertexVisionClient, VisionExtractionError
from carbon.core.config import Settings

_GOOD_JSON = (
    '{"origin": "Leeds", "destination": "York", "mode": "rail", '
    '"date": "2026-06-01", "fare": 9.0}'
)


def _settings() -> Settings:
    return Settings(gcp_project_id="test-project", _env_file=None)


def _client(**kwargs: object) -> VertexVisionClient:
    return VertexVisionClient(_settings(), backoff_s=0.0, **kwargs)  # type: ignore[arg-type]


async def test_extract_parses_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid JSON response is parsed into a TicketExtraction."""
    client = _client()
    monkeypatch.setattr(client, "_call_sync", lambda *a, **k: _GOOD_JSON)

    result = await client.extract(image_bytes=b"img", mime_type="image/png")

    assert result.origin == "Leeds"
    assert result.mode == "rail"
    assert result.fare == 9.0


async def test_extract_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient failure is retried and the next success is returned."""
    client = _client(max_retries=2)
    calls = {"n": 0}

    def flaky(*_a: object, **_k: object) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("slow")
        return _GOOD_JSON

    monkeypatch.setattr(client, "_call_sync", flaky)

    result = await client.extract(image_bytes=b"img", mime_type="image/png")

    assert result.destination == "York"
    assert calls["n"] == 2


async def test_extract_invalid_json_raises_after_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unparseable output exhausts retries and raises a vision error."""
    client = _client(max_retries=1)
    monkeypatch.setattr(client, "_call_sync", lambda *a, **k: "not json")

    with pytest.raises(VisionExtractionError):
        await client.extract(image_bytes=b"img", mime_type="image/png")
