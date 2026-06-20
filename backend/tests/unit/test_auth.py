# SPDX-License-Identifier: MIT
"""Auth dependency tests: valid / invalid / missing / malformed tokens."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import FakeVerifier, build_app

_BODY = {"domain": "transport", "mode": "car", "distance_km": 100.0}


def test_valid_token_is_accepted() -> None:
    """A token the verifier accepts yields a 200."""
    client = TestClient(build_app(verifier=FakeVerifier(uid="abc")))
    resp = client.post(
        "/api/footprint", json=_BODY, headers={"Authorization": "Bearer good"}
    )
    assert resp.status_code == 200


def test_forged_or_expired_token_is_rejected() -> None:
    """A token the verifier rejects yields a 401 envelope."""
    client = TestClient(build_app(verifier=FakeVerifier()))
    resp = client.post(
        "/api/footprint", json=_BODY, headers={"Authorization": "Bearer bad"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_missing_header_is_rejected() -> None:
    """No Authorization header yields a 401."""
    client = TestClient(build_app())
    resp = client.post("/api/footprint", json=_BODY)
    assert resp.status_code == 401


def test_malformed_scheme_is_rejected() -> None:
    """A non-bearer Authorization scheme yields a 401."""
    client = TestClient(build_app())
    resp = client.post(
        "/api/footprint", json=_BODY, headers={"Authorization": "Basic abc"}
    )
    assert resp.status_code == 401
