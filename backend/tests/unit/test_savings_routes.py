# SPDX-License-Identifier: MIT
"""Contract + behaviour tests for the savings write endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from carbon.adapters.leaderboard_store import InMemoryLeaderboardStore
from carbon.adapters.profile_store import InMemoryProfileStore
from carbon.adapters.progress_store import InMemoryGamificationStateStore
from carbon.adapters.savings_store import InMemorySavingsStore
from carbon.application.leaderboard import LeaderboardService
from carbon.models.schemas import TicketExtraction
from tests.unit.conftest import (
    FakeDistance,
    FakePublisher,
    FakeVision,
    build_app,
)

_AUTH = {"Authorization": "Bearer good"}
_PNG = ("ticket.png", b"fake-image-bytes", "image/png")


def _wired_app(
    *,
    savings_store: InMemorySavingsStore | None = None,
    profile_store: InMemoryProfileStore | None = None,
    state_store: InMemoryGamificationStateStore | None = None,
    publisher: FakePublisher | None = None,
    vision_client: FakeVision | None = None,
    distance_provider: FakeDistance | None = None,
) -> FastAPI:
    """Build an app with the full savings/social wiring (all in-memory)."""
    return build_app(
        publisher=publisher,
        state_store=state_store or InMemoryGamificationStateStore(),
        leaderboard=LeaderboardService(InMemoryLeaderboardStore()),
        savings_store=savings_store or InMemorySavingsStore(),
        profile_store=profile_store or InMemoryProfileStore(),
        vision_client=vision_client,
        distance_provider=distance_provider,
    )


def test_savings_success_matches_contract() -> None:
    """A manual carpool entry returns the exact savings response shape."""
    client = TestClient(_wired_app())
    body = {"source": "manual", "mode": "carpool", "distance_km": 30.0, "passengers": 3}

    resp = client.post("/api/savings", json=body, headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {
        "kg_co2e_saved",
        "verified",
        "points_awarded",
        "badges_unlocked",
        "streak_days",
        "request_id",
    }
    assert data["kg_co2e_saved"] == 3.414
    assert data["verified"] is False
    assert data["points_awarded"] == 12  # 10 base + 2 first-day streak bonus
    assert data["streak_days"] == 1
    assert data["badges_unlocked"] == []


def test_savings_idempotency_key_dedupes_retry() -> None:
    """A retried submit with the same Idempotency-Key scores and records once."""
    savings_store = InMemorySavingsStore()
    profile_store = InMemoryProfileStore()
    client = TestClient(
        _wired_app(savings_store=savings_store, profile_store=profile_store)
    )
    body = {"source": "manual", "mode": "carpool", "distance_km": 30.0, "passengers": 3}
    headers = {**_AUTH, "Idempotency-Key": "submit-123"}

    first = client.post("/api/savings", json=body, headers=headers)
    second = client.post("/api/savings", json=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    # The retry is recognised as a replay: zero new points, same saving value.
    assert first.json()["points_awarded"] == 12
    assert second.json()["points_awarded"] == 0
    assert second.json()["kg_co2e_saved"] == first.json()["kg_co2e_saved"]
    # Non-idempotent side effects ran exactly once.
    assert len(savings_store.records) == 1
    assert profile_store.profiles["user-1"].total_kg_co2e_saved == 3.414


def test_savings_distinct_idempotency_keys_each_count() -> None:
    """Different Idempotency-Keys are distinct submits and both count."""
    savings_store = InMemorySavingsStore()
    client = TestClient(_wired_app(savings_store=savings_store))
    body = {"source": "manual", "mode": "bus", "distance_km": 20.0}

    first = client.post(
        "/api/savings", json=body, headers={**_AUTH, "Idempotency-Key": "a"}
    )
    second = client.post(
        "/api/savings", json=body, headers={**_AUTH, "Idempotency-Key": "b"}
    )

    assert first.json()["points_awarded"] > 0
    assert second.json()["points_awarded"] > 0
    assert len(savings_store.records) == 2


def test_ticket_rejects_oversized_content_length_before_buffering() -> None:
    """A declared Content-Length over the cap returns 413 before any read."""
    vision = FakeVision()
    client = TestClient(
        build_app(
            state_store=InMemoryGamificationStateStore(),
            savings_store=InMemorySavingsStore(),
            vision_client=vision,
            distance_provider=FakeDistance(),
            max_image_bytes=8,
        )
    )

    resp = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)

    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "payload_too_large"
    # Rejected before the (expensive) vision model is ever invoked.
    assert vision.calls == []


def test_savings_requires_auth() -> None:
    """A missing bearer token returns the 401 envelope."""
    client = TestClient(_wired_app())
    body = {"source": "manual", "mode": "rail", "distance_km": 10.0}

    resp = client.post("/api/savings", json=body)

    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_savings_records_and_increments_profile_total() -> None:
    """A saving is persisted and added to the user's lifetime total."""
    savings_store = InMemorySavingsStore()
    profile_store = InMemoryProfileStore()
    client = TestClient(
        _wired_app(savings_store=savings_store, profile_store=profile_store)
    )
    body = {"source": "manual", "mode": "bus", "distance_km": 20.0}

    resp = client.post("/api/savings", json=body, headers=_AUTH)

    assert resp.status_code == 200
    assert len(savings_store.records) == 1
    assert savings_store.records[0].kg_co2e_saved == 1.3686
    profile = profile_store.profiles["user-1"]
    assert profile.total_kg_co2e_saved == 1.3686


def test_import_aggregates_rows() -> None:
    """A batch import sums per-row savings and reports rows imported."""
    client = TestClient(_wired_app())
    body = {
        "rows": [
            {"date": "2026-06-01", "distance_km": 10.0, "passengers": 2},
            {"distance_km": 30.0, "passengers": 3},
        ]
    }

    resp = client.post("/api/savings/import", json=body, headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {
        "total_kg_co2e_saved",
        "rows_imported",
        "points_awarded",
        "badges_unlocked",
        "streak_days",
        "request_id",
    }
    assert data["rows_imported"] == 2
    assert data["total_kg_co2e_saved"] == 4.2675  # 0.8535 + 3.414


def test_ticket_success_returns_verified_savings_and_extraction() -> None:
    """A ticket upload yields a verified saving, bonus points, and extraction."""
    vision = FakeVision(
        extraction=TicketExtraction(
            origin="Leeds", destination="York", mode="rail", date="2026-06-01", fare=9.0
        )
    )
    client = TestClient(
        _wired_app(
            vision_client=vision,
            distance_provider=FakeDistance(distance_km=50.0),
        )
    )

    resp = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["kg_co2e_saved"] == 6.7605  # rail, 50 km
    assert data["points_awarded"] == 27  # 12 + 15 verification bonus
    assert "verified_rider" in data["badges_unlocked"]
    assert data["extraction"] == {
        "origin": "Leeds",
        "destination": "York",
        "mode": "rail",
        "date": "2026-06-01",
        "fare": 9.0,
    }


def test_ticket_duplicate_image_rejected() -> None:
    """Submitting the same image twice is rejected with 409."""
    client = TestClient(
        _wired_app(vision_client=FakeVision(), distance_provider=FakeDistance())
    )

    first = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)
    second = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "duplicate_ticket"


def test_ticket_unreadable_returns_422() -> None:
    """A vision failure surfaces as a 422 ticket_unreadable envelope."""
    client = TestClient(
        _wired_app(
            vision_client=FakeVision(fail=True), distance_provider=FakeDistance()
        )
    )

    resp = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "ticket_unreadable"


def test_ticket_distance_unavailable_returns_422() -> None:
    """A distance failure surfaces as a 422 distance_unavailable envelope."""
    client = TestClient(
        _wired_app(
            vision_client=FakeVision(), distance_provider=FakeDistance(fail=True)
        )
    )

    resp = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "distance_unavailable"


def test_ticket_unsupported_media_type_rejected() -> None:
    """A non-image upload is rejected with 415 before any model call."""
    vision = FakeVision()
    client = TestClient(
        _wired_app(vision_client=vision, distance_provider=FakeDistance())
    )
    pdf = ("ticket.pdf", b"%PDF-1.4", "application/pdf")

    resp = client.post("/api/savings/ticket", files={"image": pdf}, headers=_AUTH)

    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "unsupported_media_type"
    assert vision.calls == []  # rejected before the model is invoked


def test_ticket_feature_unavailable_without_adapters() -> None:
    """Without vision/maps adapters the ticket endpoint fails closed with 503."""
    client = TestClient(build_app(state_store=InMemoryGamificationStateStore()))

    resp = client.post("/api/savings/ticket", files={"image": _PNG}, headers=_AUTH)

    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "feature_unavailable"


def test_savings_succeeds_with_no_optional_stores() -> None:
    """With no stores wired the saving still returns (zero points, no badges)."""
    client = TestClient(build_app())
    body = {"source": "manual", "mode": "rail", "distance_km": 40.0}

    resp = client.post("/api/savings", json=body, headers=_AUTH)

    assert resp.status_code == 200
    data = resp.json()
    assert data["kg_co2e_saved"] == 5.4084  # rail @ 40km: 6.828 - 1.4196
    assert data["points_awarded"] == 0
    assert data["badges_unlocked"] == []


class _BrokenSavingsStore(InMemorySavingsStore):
    """A savings store whose writes always fail (to exercise best-effort)."""

    async def write_record(self, record: object) -> None:
        raise RuntimeError("firestore down")


class _BrokenProfileStore(InMemoryProfileStore):
    """A profile store whose total update fails (to exercise best-effort)."""

    async def add_savings(self, uid: str, kg_co2e_saved: float) -> None:
        raise RuntimeError("firestore down")


def test_savings_best_effort_side_effects_never_fail_request() -> None:
    """A failing record write or total update does not break the response."""
    client = TestClient(
        _wired_app(
            savings_store=_BrokenSavingsStore(),
            profile_store=_BrokenProfileStore(),
        )
    )
    body = {"source": "manual", "mode": "bus", "distance_km": 20.0}

    resp = client.post("/api/savings", json=body, headers=_AUTH)

    assert resp.status_code == 200
    assert resp.json()["kg_co2e_saved"] == 1.3686
