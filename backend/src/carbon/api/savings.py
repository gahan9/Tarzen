# SPDX-License-Identifier: MIT
"""Carbon-savings API routes (avoided emissions vs a solo-car baseline).

Three write endpoints:

* ``POST /api/savings`` — a single manual/carpool entry.
* ``POST /api/savings/import`` — a batch of carpool rows from a CSV import.
* ``POST /api/savings/ticket`` — a transit-ticket image that is parsed by a
  vision model and distance-resolved via Maps, yielding a *verified* saving that
  earns an anti-cheat verification bonus.

Each endpoint computes the saving deterministically, scores points live in the
request path (idempotent via the processed-event ledger), records a
data-minimized entry, and best-effort publishes an analytics event. Image
uploads are guarded by a content-type allow-list and a size cap; image bytes are
never logged and the same image cannot be submitted twice (hash dedupe).
"""

from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile

from carbon.adapters.maps import DistanceError
from carbon.adapters.pubsub import EventPublisher, FootprintEvent, build_event
from carbon.adapters.savings_store import (
    SavingsStore,
    build_savings_record,
)
from carbon.adapters.vision import ALLOWED_IMAGE_TYPES, VisionExtractionError
from carbon.api.auth import require_uid
from carbon.api.container import Dependencies
from carbon.api.errors import ApiError
from carbon.api.rate_limit import enforce_body_size
from carbon.application.boards import boards_for
from carbon.application.live_scoring import LiveScorer, ScoringOutcome
from carbon.domain.savings import SavingsResult
from carbon.models.schemas import (
    ErrorEnvelope,
    SavingsImportRequest,
    SavingsImportResponse,
    SavingsRequest,
    SavingsResponse,
    TicketExtraction,
    TicketResponse,
)

_LOGGER = logging.getLogger(__name__)

router = APIRouter(tags=["savings"])

_SAVINGS_DOMAIN = "savings"
_CARPOOL_MODE = "carpool"
# Generous cap for JSON savings bodies (a 500-row import is well under this).
_MAX_SAVINGS_BODY_BYTES = 128_000


def _request_id(request: Request) -> str:
    """Return the correlation id stashed on the request."""
    return str(getattr(request.state, "request_id", "unknown"))


def _scoring_fields(outcome: ScoringOutcome | None) -> tuple[int, int, list[str]]:
    """Project a scoring outcome to (points, streak, badges) for responses."""
    if outcome is None:
        return 0, 0, []
    return (
        outcome.delta.points_awarded,
        outcome.delta.streak_days,
        list(outcome.delta.badges_unlocked),
    )


async def _resolve_member(deps: Dependencies, uid: str, region: str) -> str:
    """Return the anonymous handle to rank on leaderboards (falls back to uid)."""
    if deps.profile_store is None:
        return uid
    profile = await deps.profile_store.get_or_create(uid, region)
    return profile.anon_handle


async def _score(
    deps: Dependencies, *, event: FootprintEvent, member: str, region: str
) -> ScoringOutcome | None:
    """Apply live, idempotent scoring if a state store is wired."""
    if deps.state_store is None:
        return None
    scorer = LiveScorer(
        state_store=deps.state_store,
        gamification=deps.gamification,
        leaderboard=deps.leaderboard,
    )
    return await scorer.score(event, member=member, boards=boards_for(region))


async def _persist_total(deps: Dependencies, uid: str, kg_saved: float) -> None:
    """Best-effort increment of the user's lifetime saved total."""
    if deps.profile_store is None:
        return
    try:
        await deps.profile_store.add_savings(uid, kg_saved)
    except Exception:  # noqa: BLE001 - profile total must never break the write
        _LOGGER.warning("savings_total_update_failed")


async def _record(
    store: SavingsStore | None,
    *,
    uid: str,
    source: str,
    mode: str,
    distance_km: float,
    kg_saved: float,
    verified: bool,
    request_id: str,
    image_hash: str | None = None,
) -> None:
    """Best-effort, data-minimized savings-record write."""
    if store is None:
        return
    try:
        await store.write_record(
            build_savings_record(
                uid=uid,
                source=source,
                mode=mode,
                distance_km=distance_km,
                kg_co2e_saved=kg_saved,
                verified=verified,
                request_id=request_id,
                image_hash=image_hash,
            )
        )
    except Exception:  # noqa: BLE001 - logging must never break the response
        _LOGGER.warning("savings_record_write_failed", extra={"rid": request_id})


async def _publish(
    publisher: EventPublisher | None, event: FootprintEvent
) -> None:
    """Best-effort Pub/Sub publish for downstream analytics."""
    if publisher is None:
        return
    try:
        await publisher.publish(event)
    except Exception:  # noqa: BLE001 - publishing must never break the response
        _LOGGER.warning("savings_publish_failed", extra={"rid": event.request_id})


@router.post(
    "/api/savings",
    response_model=SavingsResponse,
    responses={
        401: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
    },
)
async def create_savings(
    payload: SavingsRequest,
    request: Request,
    uid: str = Depends(require_uid),
) -> SavingsResponse:
    """Record a single manual/carpool saving and score it live."""
    deps: Dependencies = request.app.state.deps
    enforce_body_size(request, max_bytes=_MAX_SAVINGS_BODY_BYTES)
    await deps.rate_limiter.acquire(uid)
    request_id = _request_id(request)

    result = deps.savings_calculator.compute(
        mode=payload.mode,
        distance_km=payload.distance_km,
        passengers=payload.passengers,
    )
    region = deps.region_resolver.resolve(request.headers)
    member = await _resolve_member(deps, uid, region)

    # A client may not self-assert verification; only the ticket path verifies.
    event = build_event(
        event_id=request_id,
        uid=uid,
        domain=_SAVINGS_DOMAIN,
        mode=payload.mode,
        kg_co2e=result.kg_co2e_saved,
        request_id=request_id,
        source=payload.source,
        verified=False,
    )
    outcome = await _score(deps, event=event, member=member, region=region)
    await _persist_total(deps, uid, result.kg_co2e_saved)
    await _record(
        deps.savings_store,
        uid=uid,
        source=payload.source,
        mode=payload.mode,
        distance_km=payload.distance_km,
        kg_saved=result.kg_co2e_saved,
        verified=False,
        request_id=request_id,
    )
    await _publish(deps.publisher, event)

    points, streak, badges = _scoring_fields(outcome)
    return SavingsResponse(
        kg_co2e_saved=result.kg_co2e_saved,
        verified=False,
        points_awarded=points,
        badges_unlocked=badges,
        streak_days=streak,
        request_id=request_id,
    )


@router.post(
    "/api/savings/import",
    response_model=SavingsImportResponse,
    responses={
        401: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
    },
)
async def import_savings(
    payload: SavingsImportRequest,
    request: Request,
    uid: str = Depends(require_uid),
) -> SavingsImportResponse:
    """Import a batch of carpool rows, scored as a single live event."""
    deps: Dependencies = request.app.state.deps
    enforce_body_size(request, max_bytes=_MAX_SAVINGS_BODY_BYTES)
    await deps.rate_limiter.acquire(uid)
    request_id = _request_id(request)

    total_saved = 0.0
    for row in payload.rows:
        result = deps.savings_calculator.compute(
            mode=_CARPOOL_MODE,
            distance_km=row.distance_km,
            passengers=row.passengers,
        )
        total_saved += result.kg_co2e_saved
    total_saved = round(total_saved, 4)

    region = deps.region_resolver.resolve(request.headers)
    member = await _resolve_member(deps, uid, region)
    event = build_event(
        event_id=request_id,
        uid=uid,
        domain=_SAVINGS_DOMAIN,
        mode=_CARPOOL_MODE,
        kg_co2e=total_saved,
        request_id=request_id,
        source="import",
        verified=False,
    )
    outcome = await _score(deps, event=event, member=member, region=region)
    await _persist_total(deps, uid, total_saved)
    await _record(
        deps.savings_store,
        uid=uid,
        source="import",
        mode=_CARPOOL_MODE,
        distance_km=0.0,
        kg_saved=total_saved,
        verified=False,
        request_id=request_id,
    )
    await _publish(deps.publisher, event)

    points, streak, badges = _scoring_fields(outcome)
    return SavingsImportResponse(
        total_kg_co2e_saved=total_saved,
        rows_imported=len(payload.rows),
        points_awarded=points,
        badges_unlocked=badges,
        streak_days=streak,
        request_id=request_id,
    )


def _validate_image(image: UploadFile, data: bytes, max_bytes: int) -> None:
    """Reject disallowed content types or oversized uploads.

    Raises:
        ApiError: 415 for an unsupported type, 413 when over the size cap.
    """
    content_type = (image.content_type or "").split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ApiError(
            415, "unsupported_media_type", "Upload a PNG, JPEG, or WebP image."
        )
    if len(data) > max_bytes:
        raise ApiError(413, "payload_too_large", "The image is too large.")
    if not data:
        raise ApiError(422, "invalid_image", "The uploaded image was empty.")


@router.post(
    "/api/savings/ticket",
    response_model=TicketResponse,
    responses={
        401: {"model": ErrorEnvelope},
        409: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        415: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    },
)
async def create_ticket_savings(
    request: Request,
    image: UploadFile = File(...),
    uid: str = Depends(require_uid),
) -> TicketResponse:
    """Parse a transit-ticket image into a verified saving with a bonus."""
    deps: Dependencies = request.app.state.deps
    await deps.rate_limiter.acquire(uid)
    request_id = _request_id(request)

    if deps.vision_client is None or deps.distance_provider is None:
        raise ApiError(
            503, "feature_unavailable", "Ticket verification is not available yet."
        )

    data = await image.read()
    _validate_image(image, data, deps.max_image_bytes)
    image_hash = hashlib.sha256(data).hexdigest()

    if deps.savings_store is not None and await deps.savings_store.is_duplicate_image(
        uid, image_hash
    ):
        raise ApiError(409, "duplicate_ticket", "This ticket was already submitted.")

    content_type = (image.content_type or "").split(";", 1)[0].strip().lower()
    try:
        extraction = await deps.vision_client.extract(
            image_bytes=data, mime_type=content_type
        )
    except VisionExtractionError as exc:
        raise ApiError(
            422, "ticket_unreadable", "Could not read trip details from the image."
        ) from exc

    mode = extraction.mode or "rail"
    try:
        distance_km = await deps.distance_provider.distance_km(
            extraction.origin or "", extraction.destination or ""
        )
    except DistanceError as exc:
        raise ApiError(
            422, "distance_unavailable", "Could not resolve the trip distance."
        ) from exc

    result: SavingsResult = deps.savings_calculator.compute(
        mode=mode, distance_km=distance_km, passengers=1
    )

    if deps.savings_store is not None:
        await deps.savings_store.reserve_image(uid, image_hash)

    region = deps.region_resolver.resolve(request.headers)
    member = await _resolve_member(deps, uid, region)
    event = build_event(
        event_id=request_id,
        uid=uid,
        domain=_SAVINGS_DOMAIN,
        mode=mode,
        kg_co2e=result.kg_co2e_saved,
        request_id=request_id,
        source="ticket",
        verified=True,
    )
    outcome = await _score(deps, event=event, member=member, region=region)
    await _persist_total(deps, uid, result.kg_co2e_saved)
    await _record(
        deps.savings_store,
        uid=uid,
        source="ticket",
        mode=mode,
        distance_km=distance_km,
        kg_saved=result.kg_co2e_saved,
        verified=True,
        request_id=request_id,
        image_hash=image_hash,
    )
    await _publish(deps.publisher, event)

    points, streak, badges = _scoring_fields(outcome)
    return TicketResponse(
        kg_co2e_saved=result.kg_co2e_saved,
        verified=True,
        points_awarded=points,
        badges_unlocked=badges,
        streak_days=streak,
        request_id=request_id,
        extraction=TicketExtraction(
            origin=extraction.origin,
            destination=extraction.destination,
            mode=extraction.mode,
            date=extraction.date,
            fare=extraction.fare,
        ),
    )
