# SPDX-License-Identifier: MIT
"""Dependency container wired onto ``app.state`` for request handlers.

Holding collaborators in one typed container keeps construction explicit and
makes tests trivial: build the app with fakes and inject them here.
"""

from __future__ import annotations

from dataclasses import dataclass

from carbon.adapters.bigquery import AnalyticsExporter
from carbon.adapters.firestore import FootprintLogStore
from carbon.adapters.pubsub import EventPublisher
from carbon.api.auth import TokenVerifier
from carbon.api.health import ReadinessProbe
from carbon.api.rate_limit import RateLimiter
from carbon.application.insights import InsightEngine
from carbon.domain.registry import TrackerRegistry


@dataclass(frozen=True, slots=True)
class Dependencies:
    """Application collaborators resolved once at startup.

    Attributes:
        registry: Active domain-tracker registry.
        insight_engine: Insight policy engine (LLM phrasing optional).
        token_verifier: Firebase ID-token verifier port.
        rate_limiter: Per-uid rate limiter.
        readiness: Readiness probe for ``/readyz``.
        log_store: Optional Firestore log writer (best-effort side effect).
        publisher: Optional Pub/Sub publisher (best-effort side effect).
        exporter: Optional BigQuery aggregate exporter.
        max_body_bytes: Hard cap on request body size.
    """

    registry: TrackerRegistry
    insight_engine: InsightEngine
    token_verifier: TokenVerifier
    rate_limiter: RateLimiter
    readiness: ReadinessProbe
    log_store: FootprintLogStore | None = None
    publisher: EventPublisher | None = None
    exporter: AnalyticsExporter | None = None
    max_body_bytes: int = 4_096
