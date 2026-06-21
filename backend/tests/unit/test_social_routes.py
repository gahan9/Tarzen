# SPDX-License-Identifier: MIT
"""Contract tests for the leaderboard and profile read endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from carbon.adapters.leaderboard_store import InMemoryLeaderboardStore
from carbon.adapters.profile_store import InMemoryProfileStore
from carbon.adapters.progress_store import InMemoryGamificationStateStore
from carbon.adapters.savings_store import InMemorySavingsStore
from carbon.application.leaderboard import LeaderboardService
from tests.unit.conftest import build_app

_AUTH = {"Authorization": "Bearer good"}
_GEO_GB = {"Authorization": "Bearer good", "x-client-geo-country": "GB"}


def _wired_app() -> FastAPI:
    """An app with savings + social fully wired in-memory."""
    return build_app(
        state_store=InMemoryGamificationStateStore(),
        leaderboard=LeaderboardService(InMemoryLeaderboardStore()),
        savings_store=InMemorySavingsStore(),
        profile_store=InMemoryProfileStore(),
    )


def test_leaderboard_matches_contract_and_marks_me() -> None:
    """After a saving, the global board lists the caller and required fields."""
    client = TestClient(_wired_app())
    body = {"source": "manual", "mode": "rail", "distance_km": 40.0}
    assert client.post("/api/savings", json=body, headers=_AUTH).status_code == 200

    resp = client.get("/api/leaderboard", params={"scope": "global"}, headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert set(data) >= {"scope", "entries", "tips"}
    assert data["scope"] == "global"
    assert isinstance(data["tips"], list)  # required, may be empty
    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    assert set(entry) >= {"anon_handle", "score", "rank"}
    assert entry["is_me"] is True
    assert entry["rank"] == 0
    assert data["my_rank"] == 0


def test_leaderboard_unavailable_without_backend() -> None:
    """Without a leaderboard service the endpoint fails closed with 503."""
    client = TestClient(build_app(state_store=InMemoryGamificationStateStore()))

    resp = client.get("/api/leaderboard", params={"scope": "global"}, headers=_AUTH)

    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "feature_unavailable"


def test_region_scope_uses_geo_header() -> None:
    """A region-scoped board echoes the resolved region from the geo header."""
    client = TestClient(_wired_app())
    body = {"source": "manual", "mode": "rail", "distance_km": 40.0}
    assert client.post("/api/savings", json=body, headers=_GEO_GB).status_code == 200

    resp = client.get("/api/leaderboard", params={"scope": "region"}, headers=_GEO_GB)

    assert resp.status_code == 200
    data = resp.json()
    assert data["scope"] == "region"
    assert data["region"] == "GB"
    assert len(data["entries"]) == 1


def test_profile_matches_contract() -> None:
    """The profile composes anon identity, gamification state, and saved total."""
    client = TestClient(_wired_app())
    body = {"source": "manual", "mode": "bus", "distance_km": 20.0}
    assert client.post("/api/savings", json=body, headers=_AUTH).status_code == 200

    resp = client.get("/api/profile", headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert set(data) >= {
        "anon_handle",
        "points",
        "streak_days",
        "badges",
        "total_kg_co2e_saved",
    }
    assert data["anon_handle"]
    assert isinstance(data["emoji"], str) and data["emoji"]
    assert data["points"] == 12
    assert data["streak_days"] == 1
    assert data["total_kg_co2e_saved"] == 1.3686


def test_profile_unavailable_without_stores() -> None:
    """Without profile/state stores the profile endpoint fails closed with 503."""
    client = TestClient(build_app())

    resp = client.get("/api/profile", headers=_AUTH)

    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "feature_unavailable"
