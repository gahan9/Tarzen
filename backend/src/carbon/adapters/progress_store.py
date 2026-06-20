# SPDX-License-Identifier: MIT
"""Durable per-user gamification state + processed-event ledger.

The store keeps each user's points/streak/badges and a ledger of already-applied
event ids so a Pub/Sub consumer can be replayed safely (at-least-once delivery
must not double-count). The :class:`GamificationStateStore` Protocol keeps the
application layer independent of Firestore; an in-memory implementation backs
unit tests so no live database is needed.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol

_PROGRESS_TIMEOUT_S = 10.0


@dataclass(frozen=True, slots=True)
class UserProgress:
    """A user's accumulated gamification state.

    Attributes:
        uid: The user the state belongs to.
        points: Lifetime points accumulated from server-validated events.
        streak_days: Current consecutive-day logging streak.
        last_active_date: ISO ``YYYY-MM-DD`` of the most recent counted day, or
            ``None`` if the user has never logged.
        badges: Sorted tuple of unlocked badge ids.
    """

    uid: str
    points: int = 0
    streak_days: int = 0
    last_active_date: str | None = None
    badges: tuple[str, ...] = ()


class GamificationStateStore(Protocol):
    """Port for persisting gamification state with replay-safe idempotency."""

    async def is_processed(self, event_id: str) -> bool:
        """Return ``True`` if ``event_id`` has already been applied."""
        ...

    async def get_state(self, uid: str) -> UserProgress:
        """Return the user's current state (a zero-state if unseen)."""
        ...

    async def apply_update(self, state: UserProgress, event_id: str) -> None:
        """Persist ``state`` and record ``event_id`` as processed."""
        ...


@dataclass(slots=True)
class InMemoryGamificationStateStore:
    """In-memory :class:`GamificationStateStore` for tests and local runs."""

    states: dict[str, UserProgress] = field(default_factory=dict)
    processed: set[str] = field(default_factory=set)

    async def is_processed(self, event_id: str) -> bool:
        """Return whether ``event_id`` is in the processed ledger."""
        return event_id in self.processed

    async def get_state(self, uid: str) -> UserProgress:
        """Return the stored state or a fresh zero-state for ``uid``."""
        return self.states.get(uid, UserProgress(uid=uid))

    async def apply_update(self, state: UserProgress, event_id: str) -> None:
        """Store the new state and mark the event processed."""
        self.states[state.uid] = state
        self.processed.add(event_id)


class FirestoreGamificationStateStore:
    """Firestore-backed :class:`GamificationStateStore`.

    State is stored one document per user; the processed-event ledger is a
    separate collection keyed by event id. The synchronous Firestore SDK is
    wrapped with :func:`asyncio.to_thread` to keep callers non-blocking.
    """

    def __init__(
        self,
        client: object,
        *,
        progress_collection: str = "gamification_progress",
        ledger_collection: str = "gamification_processed_events",
    ) -> None:
        """Initialise with an injected Firestore client and collection names."""
        self._client = client
        self._progress_collection = progress_collection
        self._ledger_collection = ledger_collection

    async def is_processed(self, event_id: str) -> bool:
        """Return whether the ledger already contains ``event_id``."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._is_processed_sync, event_id),
            timeout=_PROGRESS_TIMEOUT_S,
        )

    async def get_state(self, uid: str) -> UserProgress:
        """Read the user's progress document, defaulting to a zero-state."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._get_state_sync, uid),
            timeout=_PROGRESS_TIMEOUT_S,
        )

    async def apply_update(self, state: UserProgress, event_id: str) -> None:
        """Persist progress and mark the event processed off the event loop."""
        await asyncio.wait_for(
            asyncio.to_thread(self._apply_update_sync, state, event_id),
            timeout=_PROGRESS_TIMEOUT_S,
        )

    def _is_processed_sync(self, event_id: str) -> bool:
        """Blocking ledger existence check."""
        doc = (
            self._client.collection(self._ledger_collection)  # type: ignore[attr-defined]
            .document(event_id)
            .get()
        )
        return bool(doc.exists)

    def _get_state_sync(self, uid: str) -> UserProgress:
        """Blocking progress read mapped to :class:`UserProgress`."""
        doc = (
            self._client.collection(self._progress_collection)  # type: ignore[attr-defined]
            .document(uid)
            .get()
        )
        if not doc.exists:
            return UserProgress(uid=uid)
        data = doc.to_dict() or {}
        return UserProgress(
            uid=uid,
            points=int(data.get("points", 0)),
            streak_days=int(data.get("streak_days", 0)),
            last_active_date=data.get("last_active_date"),
            badges=tuple(data.get("badges", ())),
        )

    def _apply_update_sync(self, state: UserProgress, event_id: str) -> None:
        """Blocking write of progress + processed-event marker."""
        client = self._client
        client.collection(self._progress_collection).document(  # type: ignore[attr-defined]
            state.uid
        ).set(
            {
                "points": state.points,
                "streak_days": state.streak_days,
                "last_active_date": state.last_active_date,
                "badges": list(state.badges),
            }
        )
        client.collection(self._ledger_collection).document(  # type: ignore[attr-defined]
            event_id
        ).set({"processed": True})
