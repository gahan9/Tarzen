# SPDX-License-Identifier: MIT
"""Unit tests for application wiring in :mod:`carbon.main`."""

from __future__ import annotations

import pytest

from carbon.adapters.leaderboard_store import (
    InMemoryLeaderboardStore,
    MemorystoreLeaderboardStore,
)
from carbon.core.config import Settings
from carbon.main import _build_leaderboard_store


def test_leaderboard_store_defaults_to_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Absent REDIS_HOST selects the per-instance in-memory store."""
    monkeypatch.setenv("GCP_PROJECT_ID", "demo-project")
    monkeypatch.delenv("REDIS_HOST", raising=False)

    store = _build_leaderboard_store(Settings(_env_file=None))

    assert isinstance(store, InMemoryLeaderboardStore)


def test_leaderboard_store_uses_memorystore_when_redis_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A configured REDIS_HOST selects the Memorystore (Redis) ZSET backend.

    Constructing the async client does not open a connection, so this exercises
    the selection seam without any live Redis.
    """
    monkeypatch.setenv("GCP_PROJECT_ID", "demo-project")
    monkeypatch.setenv("REDIS_HOST", "10.0.0.5")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_PASSWORD", "auth-string")
    monkeypatch.setenv("REDIS_USE_TLS", "true")

    store = _build_leaderboard_store(Settings(_env_file=None))

    assert isinstance(store, MemorystoreLeaderboardStore)
