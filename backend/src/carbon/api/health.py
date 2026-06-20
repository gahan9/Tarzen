# SPDX-License-Identifier: MIT
"""Liveness and readiness endpoints.

``/healthz`` is a cheap liveness probe. ``/readyz`` runs registered readiness
checks (e.g. Firestore/Vertex reachability) and reports 503 if any fail. Checks
are injected so they are fully mockable in tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request, Response

ReadinessCheck = Callable[[], Awaitable[bool]]


class ReadinessProbe:
    """Runs a set of named async readiness checks concurrently."""

    def __init__(self, checks: dict[str, ReadinessCheck]) -> None:
        """Initialise with a mapping of check name to async predicate."""
        self._checks = checks

    async def run(self) -> dict[str, bool]:
        """Execute all checks concurrently, returning per-check results.

        A check that raises is treated as a failure rather than propagating.
        """

        async def _safe(check: ReadinessCheck) -> bool:
            try:
                return await check()
            except Exception:  # noqa: BLE001 - any failure means "not ready"
                return False

        names = list(self._checks)
        results = await asyncio.gather(*(_safe(self._checks[n]) for n in names))
        return dict(zip(names, results, strict=True))


router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe: the process is up and serving."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request, response: Response) -> dict[str, object]:
    """Readiness probe: dependencies are reachable.

    Returns 200 when all checks pass, otherwise 503 with per-check detail.
    """
    probe: ReadinessProbe = request.app.state.deps.readiness
    results = await probe.run()
    ready = all(results.values())
    if not ready:
        response.status_code = 503
    return {"status": "ready" if ready else "not_ready", "checks": results}
