# SPDX-License-Identifier: MIT
"""FastAPI application factory and production dependency wiring.

``create_app`` builds the ASGI app with CORS locked to configured origins,
structured logging, the error-envelope handlers, and the footprint/health
routes. Collaborators are injected via :class:`Dependencies` so tests can supply
fakes; production wiring constructs the real GCP-backed adapters.
"""

from __future__ import annotations

import asyncio

import firebase_admin
import google.cloud.pubsub_v1 as pubsub_v1
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore

from carbon.adapters.firestore import FirestoreFootprintStore
from carbon.adapters.gemini import VertexGeminiClient
from carbon.adapters.pubsub import PubSubEventPublisher
from carbon.api import health
from carbon.api import routes as footprint_routes
from carbon.api.auth import FirebaseTokenVerifier
from carbon.api.container import Dependencies
from carbon.api.errors import (
    ApiError,
    api_error_handler,
    domain_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from carbon.api.health import ReadinessProbe
from carbon.api.logging_middleware import StructuredLoggingMiddleware
from carbon.api.rate_limit import RateLimiter
from carbon.application.insights import InsightEngine
from carbon.core.config import Settings, get_settings
from carbon.core.logging import configure_logging
from carbon.domain.errors import DomainError
from carbon.domain.registry import build_default_registry

_FOOTPRINT_EVENTS_TOPIC = "footprint-events"


def _build_production_readiness(
    fs_client: firestore.Client,
) -> ReadinessProbe:
    """Construct readiness checks for live dependencies."""

    async def firestore_ready() -> bool:
        await asyncio.to_thread(lambda: list(fs_client.collections()))
        return True

    async def vertex_ready() -> bool:
        # Construction of the client validates configuration; a full round-trip
        # is intentionally avoided to keep readiness cheap.
        return True

    return ReadinessProbe({"firestore": firestore_ready, "vertex": vertex_ready})


def build_production_dependencies(settings: Settings) -> Dependencies:
    """Construct real GCP-backed collaborators for serving traffic."""
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()

    gemini = VertexGeminiClient(settings)
    engine = InsightEngine(gemini, llm_enabled=True)

    fs_client = firestore.Client(project=settings.gcp_project_id)
    log_store = FirestoreFootprintStore(fs_client)

    publisher_client = pubsub_v1.PublisherClient()
    topic_path = publisher_client.topic_path(
        settings.gcp_project_id, _FOOTPRINT_EVENTS_TOPIC
    )
    publisher = PubSubEventPublisher(publisher_client, topic_path=topic_path)

    return Dependencies(
        registry=build_default_registry(),
        insight_engine=engine,
        token_verifier=FirebaseTokenVerifier(),
        rate_limiter=RateLimiter(),
        readiness=_build_production_readiness(fs_client),
        log_store=log_store,
        publisher=publisher,
        exporter=None,
    )


def _register_handlers(app: FastAPI) -> None:
    """Wire the exception handlers that produce the error envelope."""
    app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)


def create_app(
    settings: Settings | None = None,
    *,
    deps: Dependencies | None = None,
) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Application settings; defaults to the cached settings.
        deps: Pre-built collaborators; when omitted, production wiring is built
            from ``settings``.

    Returns:
        The configured :class:`FastAPI` app.
    """
    settings = settings or get_settings()
    configure_logging(settings.app_log_level)

    app = FastAPI(
        title="Carbon Footprint Platform API",
        version="0.1.0",
        description="Deterministic footprint engine with policy-gated insights.",
    )
    app.state.settings = settings
    app.state.deps = deps or build_production_dependencies(settings)

    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    )

    _register_handlers(app)
    app.include_router(health.router)
    app.include_router(footprint_routes.router)
    return app
