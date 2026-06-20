# SPDX-License-Identifier: MIT
"""Security response-header middleware (defense in depth).

Applies hardening headers to every response so a misconfigured client, a
reflected payload, or an embedded context cannot escalate into a browser-side
attack. The API serves JSON only, so the default Content-Security-Policy is
maximally restrictive (``default-src 'none'``); the interactive API docs
(``/docs``, ``/redoc``) need to load Swagger/ReDoc assets from a CDN, so those
paths receive a narrower, docs-specific policy instead.

Headers are written with ``setdefault`` semantics so a handler that
deliberately sets its own value (for example a future endpoint that must embed
content) is never silently overridden.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Strict policy for JSON API responses: the API never returns HTML that loads
# sub-resources, so nothing needs to be allowed.
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"

# Swagger UI / ReDoc load their bundle and inline styles from jsDelivr.
_DOCS_CSP = (
    "default-src 'none'; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' https://fastapi.tiangolo.com data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
)

# Documentation routes that must use the relaxed CSP above.
_DOCS_PREFIXES = ("/docs", "/redoc")

# Headers applied verbatim to every response regardless of route.
_STATIC_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    # Cloud Run terminates TLS, so HSTS is always honoured in production. It is
    # a no-op on plaintext localhost, so it is safe to send unconditionally.
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


def _csp_for_path(path: str) -> str:
    """Return the Content-Security-Policy appropriate for the request path."""
    if any(path.startswith(prefix) for prefix in _DOCS_PREFIXES):
        return _DOCS_CSP
    return _API_CSP


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardening headers (CSP, framing, MIME, referrer) to responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Run the handler, then layer security headers onto its response."""
        response = await call_next(request)
        for header, value in _STATIC_HEADERS.items():
            response.headers.setdefault(header, value)
        response.headers.setdefault(
            "Content-Security-Policy", _csp_for_path(request.url.path)
        )
        return response
