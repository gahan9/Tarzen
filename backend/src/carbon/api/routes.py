# SPDX-License-Identifier: MIT
"""Footprint API routes.

Exposes ``POST /api/footprint``: authenticate, enforce abuse controls, run the
deterministic tracker, attach a policy-gated insight, emit best-effort
side-effects (log + event), and return the typed response.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from carbon.adapters.firestore import FootprintLogStore, build_log_record
from carbon.adapters.pubsub import EventPublisher, build_event
from carbon.api.auth import require_uid
from carbon.api.container import Dependencies
from carbon.api.rate_limit import enforce_body_size
from carbon.application.insights import InsightEngine, InsightInput
from carbon.domain.models import FootprintResult
from carbon.models.schemas import (
    BreakdownItem,
    ErrorEnvelope,
    FootprintRequest,
    FootprintResponse,
    Insight,
)

_LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["footprint"])


def _primary_quantity(request: FootprintRequest) -> float | None:
    """Return the single activity magnitude supplied for the request's domain.

    Exactly one quantity field is populated per request; this collapses them to
    the figure the insight engine frames (e.g. distance for transport, kWh for
    energy).
    """
    if request.distance_km is not None:
        return request.distance_km
    if request.kwh is not None:
        return request.kwh
    if request.servings is not None:
        return float(request.servings)
    if request.spend is not None:
        return request.spend
    return request.waste_kg


async def _log_footprint(
    store: FootprintLogStore | None,
    *,
    uid: str,
    request: FootprintRequest,
    result: FootprintResult,
    request_id: str,
) -> None:
    """Best-effort, data-minimized Firestore log write."""
    if store is None:
        return
    try:
        await store.write_log(
            build_log_record(
                uid=uid,
                domain=request.domain,
                mode=request.mode,
                kg_co2e=result.kg_co2e,
                request_id=request_id,
            )
        )
    except Exception:  # noqa: BLE001 - logging must never break the response
        _LOGGER.warning("footprint_log_write_failed", extra={"request_id": request_id})


async def _publish_footprint(
    publisher: EventPublisher | None,
    *,
    uid: str,
    request: FootprintRequest,
    result: FootprintResult,
    request_id: str,
) -> None:
    """Best-effort Pub/Sub event publish for async aggregation."""
    if publisher is None:
        return
    try:
        await publisher.publish(
            build_event(
                event_id=request_id,
                uid=uid,
                domain=request.domain,
                mode=request.mode,
                kg_co2e=result.kg_co2e,
                request_id=request_id,
            )
        )
    except Exception:  # noqa: BLE001 - publishing must never break the response
        _LOGGER.warning("footprint_publish_failed", extra={"request_id": request_id})


@router.post(
    "/api/footprint",
    response_model=FootprintResponse,
    responses={
        400: {"model": ErrorEnvelope},
        401: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
    },
)
async def create_footprint(
    payload: FootprintRequest,
    request: Request,
    uid: str = Depends(require_uid),
) -> FootprintResponse:
    """Compute a footprint and an accompanying sustainability insight."""
    deps: Dependencies = request.app.state.deps
    enforce_body_size(request, max_bytes=deps.max_body_bytes)
    await deps.rate_limiter.acquire(uid)

    request_id = str(getattr(request.state, "request_id", "unknown"))

    tracker = deps.registry.get(payload.domain)
    params = payload.model_dump(exclude_none=True, exclude={"domain"})
    result = tracker.compute(params)

    engine: InsightEngine = deps.insight_engine
    insight = await engine.generate(
        InsightInput(
            result=result,
            mode=payload.mode,
            distance_km=payload.distance_km,
            passengers=payload.passengers,
            quantity=_primary_quantity(payload),
        )
    )
    request.state.llm_used = insight.llm_used

    await _log_footprint(
        deps.log_store,
        uid=uid,
        request=payload,
        result=result,
        request_id=request_id,
    )
    await _publish_footprint(
        deps.publisher,
        uid=uid,
        request=payload,
        result=result,
        request_id=request_id,
    )

    return FootprintResponse(
        kg_co2e=result.kg_co2e,
        breakdown=[
            BreakdownItem(label=item.label, kg_co2e=item.kg_co2e)
            for item in result.breakdown
        ],
        insight=Insight(
            message=insight.message,
            benchmark=insight.benchmark,
            actions=insight.actions,
            needs_context=insight.needs_context,
            llm_used=insight.llm_used,
        ),
        request_id=request_id,
    )
