# SPDX-License-Identifier: MIT
"""Rate limiter and request-size cap tests."""

from __future__ import annotations

import pytest

from carbon.api.errors import ApiError
from carbon.api.rate_limit import RateLimiter, enforce_body_size


async def test_rate_limiter_allows_then_blocks() -> None:
    """Requests within budget pass; the next one is rejected with 429."""
    limiter = RateLimiter(max_requests=2, window_s=60.0)

    await limiter.acquire("uid-1")
    await limiter.acquire("uid-1")
    with pytest.raises(ApiError) as exc:
        await limiter.acquire("uid-1")

    assert exc.value.status_code == 429
    assert exc.value.code == "rate_limited"


async def test_rate_limiter_is_per_key() -> None:
    """Separate identities have independent budgets."""
    limiter = RateLimiter(max_requests=1, window_s=60.0)
    await limiter.acquire("uid-1")
    await limiter.acquire("uid-2")  # different key, must not be blocked


class _Req:
    """Minimal stand-in exposing the headers attribute used by the guard."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def test_enforce_body_size_rejects_large_payload() -> None:
    """A Content-Length above the cap raises 413."""
    req = _Req({"content-length": "100000"})
    with pytest.raises(ApiError) as exc:
        enforce_body_size(req, max_bytes=4096)  # type: ignore[arg-type]
    assert exc.value.status_code == 413


def test_enforce_body_size_allows_small_payload() -> None:
    """A small Content-Length passes without error."""
    req = _Req({"content-length": "100"})
    enforce_body_size(req, max_bytes=4096)  # type: ignore[arg-type]
