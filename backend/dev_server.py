# SPDX-License-Identifier: MIT
"""Local ASGI app with in-memory adapters (no GCP / Firebase / Vertex).

Run from ``backend/``::

    .venv\\Scripts\\python -m uvicorn dev_server:app \\
        --host 127.0.0.1 --port 8080 --reload

Pair with the web app (``npm run dev`` in ``frontend/``), which proxies ``/api``
to this process. Auth uses the unit-test fake verifier: send
``Authorization: Bearer good`` (any non-``bad`` token maps to ``user-1``).
"""

from __future__ import annotations

from tests.unit.conftest import (
    FakeDistance,
    FakePublisher,
    FakeVision,
    build_app,
)

from carbon.adapters.leaderboard_store import InMemoryLeaderboardStore
from carbon.adapters.profile_store import InMemoryProfileStore
from carbon.adapters.progress_store import InMemoryGamificationStateStore
from carbon.adapters.savings_store import InMemorySavingsStore
from carbon.application.leaderboard import LeaderboardService

app = build_app(
    publisher=FakePublisher(),
    state_store=InMemoryGamificationStateStore(),
    leaderboard=LeaderboardService(InMemoryLeaderboardStore()),
    savings_store=InMemorySavingsStore(),
    profile_store=InMemoryProfileStore(),
    vision_client=FakeVision(),
    distance_provider=FakeDistance(),
)
