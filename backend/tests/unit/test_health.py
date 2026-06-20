# SPDX-License-Identifier: MIT
"""Liveness/readiness endpoint tests with injected probe checks."""

from __future__ import annotations

from fastapi.testclient import TestClient

from carbon.api.health import ReadinessProbe
from tests.unit.conftest import build_app


def test_healthz_is_ok(client: TestClient) -> None:
    """Liveness always reports ok."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_all_checks_pass() -> None:
    """Readiness reports 200 when every check passes."""

    async def ok() -> bool:
        return True

    app = build_app(readiness=ReadinessProbe({"firestore": ok, "vertex": ok}))
    resp = TestClient(app).get("/readyz")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_readyz_failing_check_returns_503() -> None:
    """Readiness reports 503 when any check fails or raises."""

    async def ok() -> bool:
        return True

    async def boom() -> bool:
        raise RuntimeError("unreachable")

    app = build_app(readiness=ReadinessProbe({"firestore": ok, "vertex": boom}))
    resp = TestClient(app).get("/readyz")

    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert body["checks"] == {"firestore": True, "vertex": False}
