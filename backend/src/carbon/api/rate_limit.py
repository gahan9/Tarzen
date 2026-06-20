# SPDX-License-Identifier: MIT
"""Per-uid rate limiting and request-size caps for the footprint endpoint.

A simple in-memory sliding-window limiter guards against cost/DoS abuse of the
LLM-backed endpoint. For multi-instance deployments this is replaced by a shared
store (Memorystore); the Protocol keeps that swap local.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from fastapi import Request

from carbon.api.errors import ApiError

DEFAULT_MAX_REQUESTS = 30
DEFAULT_WINDOW_S = 60.0
DEFAULT_MAX_BODY_BYTES = 4_096


class RateLimiter:
    """In-memory sliding-window rate limiter keyed by an arbitrary identity."""

    def __init__(
        self,
        *,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        window_s: float = DEFAULT_WINDOW_S,
    ) -> None:
        """Configure the window size and request budget per key."""
        self._max_requests = max_requests
        self._window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> None:
        """Record a hit for ``key``.

        Raises:
            ApiError: 429 when the per-window budget is exceeded.
        """
        now = time.monotonic()
        async with self._lock:
            hits = self._hits[key]
            cutoff = now - self._window_s
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self._max_requests:
                raise ApiError(
                    429, "rate_limited", "Too many requests; please slow down."
                )
            hits.append(now)


def enforce_body_size(
    request: Request, *, max_bytes: int = DEFAULT_MAX_BODY_BYTES
) -> None:
    """Reject oversized requests using the Content-Length header.

    Raises:
        ApiError: 413 when the declared body exceeds ``max_bytes``.
    """
    raw_length = request.headers.get("content-length")
    if raw_length is None:
        return
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise ApiError(400, "invalid_request", "Invalid Content-Length.") from exc
    if length > max_bytes:
        raise ApiError(413, "payload_too_large", "Request body is too large.")
