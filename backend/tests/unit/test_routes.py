# SPDX-License-Identifier: MIT
"""API contract conformance tests for POST /api/footprint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import FakeLogStore, FakePublisher, build_app

_AUTH = {"Authorization": "Bearer good"}
_BODY = {"domain": "transport", "mode": "car", "distance_km": 100.0}


def test_footprint_success_matches_contract(client: TestClient) -> None:
    """A valid request returns the exact success response shape."""
    resp = client.post("/api/footprint", json=_BODY, headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert data["kg_co2e"] == 17.07
    assert isinstance(data["breakdown"], list)
    assert set(data["breakdown"][0]) == {"label", "kg_co2e"}
    assert set(data["insight"]) == {
        "message",
        "benchmark",
        "actions",
        "needs_context",
        "llm_used",
    }
    assert data["insight"]["llm_used"] is False
    assert isinstance(data["request_id"], str) and data["request_id"]


def test_footprint_requires_auth(client: TestClient) -> None:
    """A missing bearer token returns the 401 error envelope."""
    resp = client.post("/api/footprint", json=_BODY)

    assert resp.status_code == 401
    err = resp.json()["error"]
    assert err["code"] == "unauthorized"
    assert set(err) == {"code", "message", "request_id"}


def test_footprint_validation_error_envelope(client: TestClient) -> None:
    """An out-of-bounds field returns the 422 error envelope."""
    bad = {"domain": "transport", "mode": "car", "distance_km": -1.0}
    resp = client.post("/api/footprint", json=bad, headers=_AUTH)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_footprint_unsupported_domain_envelope(client: TestClient) -> None:
    """An unregistered domain returns the 404 unsupported_domain envelope."""
    body = {"domain": "energy", "mode": "car", "distance_km": 10.0}
    resp = client.post("/api/footprint", json=body, headers=_AUTH)

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "unsupported_domain"


def test_footprint_side_effects_are_invoked() -> None:
    """A successful request writes a log and publishes an event."""
    log_store = FakeLogStore()
    publisher = FakePublisher()
    app = build_app(log_store=log_store, publisher=publisher)

    resp = TestClient(app).post("/api/footprint", json=_BODY, headers=_AUTH)

    assert resp.status_code == 200
    assert len(log_store.records) == 1
    assert log_store.records[0].kg_co2e == 17.07
    assert len(publisher.events) == 1
