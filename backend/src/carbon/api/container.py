# SPDX-License-Identifier: MIT
"""Dependency container wired onto ``app.state`` for request handlers.

Holding collaborators in one typed container keeps construction explicit and
makes tests trivial: build the app with fakes and inject them here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from carbon.adapters.bigquery import AnalyticsExporter
from carbon.adapters.firestore import FootprintLogStore
from carbon.adapters.maps import DistanceProvider
from carbon.adapters.profile_store import ProfileStore
from carbon.adapters.progress_store import GamificationStateStore
from carbon.adapters.pubsub import EventPublisher
from carbon.adapters.region import HeaderRegionResolver, RegionResolver
from carbon.adapters.savings_store import SavingsStore
from carbon.adapters.vision import VisionClient
from carbon.api.auth import TokenVerifier
from carbon.api.health import ReadinessProbe
from carbon.api.rate_limit import RateLimiter
from carbon.application.gamification import GamificationService
from carbon.application.insights import InsightEngine
from carbon.application.leaderboard import LeaderboardService
from carbon.domain.registry import TrackerRegistry, build_savings_calculator
from carbon.domain.savings import SavingsCalculator


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
        savings_calculator: Pure avoided-emissions calculator (always present).
        gamification: Pure scoring service (always present).
        region_resolver: Maps request headers to a coarse region key.
        state_store: Optional gamification state store (enables live scoring).
        leaderboard: Optional leaderboard service (enables board updates/reads).
        savings_store: Optional savings record store with image dedupe.
        profile_store: Optional anonymous profile store.
        vision_client: Optional multimodal client for ticket extraction.
        distance_provider: Optional Maps distance resolver for tickets.
        leaderboard_top: Number of top entries the leaderboard endpoint returns.
        max_image_bytes: Hard cap on uploaded ticket-image size.
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
    savings_calculator: SavingsCalculator = field(
        default_factory=build_savings_calculator
    )
    gamification: GamificationService = field(default_factory=GamificationService)
    region_resolver: RegionResolver = field(default_factory=HeaderRegionResolver)
    state_store: GamificationStateStore | None = None
    leaderboard: LeaderboardService | None = None
    savings_store: SavingsStore | None = None
    profile_store: ProfileStore | None = None
    vision_client: VisionClient | None = None
    distance_provider: DistanceProvider | None = None
    leaderboard_top: int = 50
    max_image_bytes: int = 5_000_000
    max_body_bytes: int = 4_096
