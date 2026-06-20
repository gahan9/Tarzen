# SPDX-License-Identifier: MIT
"""Shared fixtures and fakes for unit tests.

All external boundaries (LLM, auth, Firestore, Pub/Sub) are replaced with
in-memory fakes so unit tests never touch the network.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from carbon.adapters.firestore import FootprintLogRecord
from carbon.adapters.gemini import GeminiError
from carbon.adapters.pubsub import FootprintEvent
from carbon.api.container import Dependencies
from carbon.api.health import ReadinessProbe
from carbon.api.rate_limit import RateLimiter
from carbon.application.insights import InsightEngine
from carbon.core.config import Settings
from carbon.domain.registry import build_default_registry
from carbon.main import create_app


class FakeVerifier:
    """Token verifier that returns a fixed uid for any token."""

    def __init__(self, uid: str = "user-1") -> None:
        self._uid = uid

    def verify(self, token: str) -> Mapping[str, Any]:
        """Return canned claims; raise on the sentinel 'bad' token."""
        if token == "bad":
            raise ValueError("invalid token")
        return {"uid": self._uid}


class FakeGemini:
    """Scriptable Gemini client: returns a canned string or raises."""

    def __init__(self, *, response: str | None = None, fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Record the call and return/raise per configuration."""
        self.calls += 1
        if self.fail:
            raise GeminiError("simulated outage")
        assert self.response is not None
        return self.response


class FakeLogStore:
    """In-memory footprint log store."""

    def __init__(self) -> None:
        self.records: list[FootprintLogRecord] = []

    async def write_log(self, record: FootprintLogRecord) -> None:
        self.records.append(record)


class FakePublisher:
    """In-memory event publisher."""

    def __init__(self) -> None:
        self.events: list[FootprintEvent] = []

    async def publish(self, event: FootprintEvent) -> str:
        self.events.append(event)
        return "msg-1"


def make_settings() -> Settings:
    """Build deterministic settings without reading any .env file."""
    return Settings(gcp_project_id="test-project", _env_file=None)


def build_app(
    *,
    verifier: FakeVerifier | None = None,
    insight_engine: InsightEngine | None = None,
    readiness: ReadinessProbe | None = None,
    log_store: FakeLogStore | None = None,
    publisher: FakePublisher | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    """Create the app wired with in-memory fakes."""
    deps = Dependencies(
        registry=build_default_registry(),
        insight_engine=insight_engine or InsightEngine(None, llm_enabled=False),
        token_verifier=verifier or FakeVerifier(),
        rate_limiter=rate_limiter or RateLimiter(),
        readiness=readiness or ReadinessProbe({}),
        log_store=log_store,
        publisher=publisher,
    )
    return create_app(make_settings(), deps=deps)


@pytest.fixture
def client() -> TestClient:
    """A TestClient over an app with default fakes (LLM disabled)."""
    return TestClient(build_app())
