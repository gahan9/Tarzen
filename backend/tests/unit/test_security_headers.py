# SPDX-License-Identifier: MIT
"""Tests for the hardening response headers applied to every response."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import build_app

_EXPECTED_STATIC = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def test_static_security_headers_present_on_every_response(
    client: TestClient,
) -> None:
    """The fixed hardening headers are attached to a normal API response."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    for header, value in _EXPECTED_STATIC.items():
        assert resp.headers[header] == value
    assert "max-age=" in resp.headers["Strict-Transport-Security"]
    assert "geolocation=()" in resp.headers["Permissions-Policy"]


def test_api_responses_use_strict_csp(client: TestClient) -> None:
    """JSON API paths receive the maximally restrictive CSP."""
    resp = client.get("/healthz")
    assert resp.headers["Content-Security-Policy"] == (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )


def test_docs_path_uses_relaxed_csp_allowing_cdn() -> None:
    """The Swagger UI route gets a CSP that permits its CDN assets."""
    client = TestClient(build_app())
    resp = client.get("/docs")
    assert resp.status_code == 200
    csp = resp.headers["Content-Security-Policy"]
    assert "https://cdn.jsdelivr.net" in csp
    assert "script-src" in csp


def test_security_headers_present_on_error_responses(client: TestClient) -> None:
    """Headers are applied even when the handler returns a non-2xx status."""
    resp = client.get("/nonexistent-route")
    assert resp.status_code == 404
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_cors_preflight_allows_client_trace_header(client: TestClient) -> None:
    """The browser preflight must permit the ``X-Trace-Id`` the web client sends.

    Regression: omitting this header from the CORS allow-list makes the browser
    block the real request, which the web app surfaces as a misleading
    "could not reach the server" error.
    """
    resp = client.options(
        "/api/footprint",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-trace-id",
        },
    )
    assert resp.status_code == 200
    allowed = resp.headers["access-control-allow-headers"].lower()
    assert "x-trace-id" in allowed
