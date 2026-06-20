# SPDX-License-Identifier: MIT
"""Request-scoped structured logging middleware.

Assigns a ``request_id`` and propagates a ``trace_id``, times each request, and
emits a single structured access log. Request and response bodies are never
read or logged, so PII and secrets stay out of logs.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_LOGGER = logging.getLogger("carbon.access")

_REQUEST_ID_HEADER = "x-request-id"
_TRACE_HEADER = "x-cloud-trace-context"


def _derive_trace_id(raw: str | None) -> str:
    """Extract the trace id from a Cloud Trace header or mint a new one."""
    if raw:
        return raw.split("/", 1)[0]
    return uuid.uuid4().hex


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Attach correlation ids and emit one structured access log per request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Wrap the request with correlation ids, timing, and structured logging."""
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex
        trace_id = _derive_trace_id(request.headers.get(_TRACE_HEADER))
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.uid = None
        request.state.llm_used = None
        request.state.gemini_latency_ms = None

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        _LOGGER.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "request_id": request_id,
                "trace_id": trace_id,
                "uid": request.state.uid,
                "route": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "latency_ms": latency_ms,
                "llm_used": request.state.llm_used,
                "gemini_latency_ms": request.state.gemini_latency_ms,
            },
        )
        response.headers[_REQUEST_ID_HEADER] = request_id
        return response
