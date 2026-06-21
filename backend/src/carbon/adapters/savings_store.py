# SPDX-License-Identifier: MIT
"""Firestore persistence for data-minimized savings records + image dedupe.

Only the minimum needed to render a user's history and to stop a ticket being
submitted twice is persisted — never the uploaded image bytes nor any extracted
free-text beyond a coarse origin/destination. Ticket dedupe is keyed by a SHA-256
hash of the image so the same receipt cannot earn points repeatedly. The
synchronous Firestore SDK is wrapped with :func:`asyncio.to_thread` to keep the
request path non-blocking; an in-memory implementation backs unit tests.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Protocol

DEFAULT_RECORDS_COLLECTION = "savings_records"
DEFAULT_DEDUPE_COLLECTION = "savings_image_hashes"
_TIMEOUT_S = 10.0


@dataclass(frozen=True, slots=True)
class SavingsRecord:
    """A data-minimized savings entry.

    Attributes:
        uid: Authenticated user id (owner of the record).
        source: Provenance (``manual``, ``import``, ``ticket``).
        mode: The lower-carbon mode used.
        distance_km: Trip distance in kilometres.
        kg_co2e_saved: Avoided emissions for the trip.
        verified: Whether the saving was server-verified.
        request_id: Correlation id for tracing.
        created_at: UTC ISO-8601 timestamp.
        image_hash: SHA-256 of the source image for verified tickets, else
            ``None``.
    """

    uid: str
    source: str
    mode: str
    distance_km: float
    kg_co2e_saved: float
    verified: bool
    request_id: str
    created_at: str
    image_hash: str | None = None


def build_savings_record(
    *,
    uid: str,
    source: str,
    mode: str,
    distance_km: float,
    kg_co2e_saved: float,
    verified: bool,
    request_id: str,
    image_hash: str | None = None,
) -> SavingsRecord:
    """Construct a savings record stamped with the current UTC time."""
    return SavingsRecord(
        uid=uid,
        source=source,
        mode=mode,
        distance_km=distance_km,
        kg_co2e_saved=kg_co2e_saved,
        verified=verified,
        request_id=request_id,
        created_at=datetime.now(UTC).isoformat(),
        image_hash=image_hash,
    )


class SavingsStore(Protocol):
    """Port for persisting savings records with image-hash dedupe."""

    async def write_record(self, record: SavingsRecord) -> None:
        """Persist a single savings record."""
        ...

    async def is_duplicate_image(self, uid: str, image_hash: str) -> bool:
        """Return ``True`` if ``uid`` already submitted this image hash."""
        ...

    async def reserve_image(self, uid: str, image_hash: str) -> None:
        """Record an image hash as seen for ``uid`` (dedupe marker)."""
        ...


@dataclass(slots=True)
class InMemorySavingsStore:
    """In-memory :class:`SavingsStore` for tests and local runs."""

    records: list[SavingsRecord] = field(default_factory=list)
    seen_hashes: set[tuple[str, str]] = field(default_factory=set)

    async def write_record(self, record: SavingsRecord) -> None:
        """Append the record to the in-memory list."""
        self.records.append(record)

    async def is_duplicate_image(self, uid: str, image_hash: str) -> bool:
        """Return whether ``(uid, image_hash)`` has been reserved."""
        return (uid, image_hash) in self.seen_hashes

    async def reserve_image(self, uid: str, image_hash: str) -> None:
        """Mark ``(uid, image_hash)`` as seen."""
        self.seen_hashes.add((uid, image_hash))


class FirestoreSavingsStore:
    """Firestore-backed :class:`SavingsStore`.

    Records live in one collection; image-hash dedupe markers live in a separate
    collection keyed by ``"{uid}:{image_hash}"`` so the existence check is a
    single document read.
    """

    def __init__(
        self,
        client: object,
        *,
        records_collection: str = DEFAULT_RECORDS_COLLECTION,
        dedupe_collection: str = DEFAULT_DEDUPE_COLLECTION,
    ) -> None:
        """Initialise with an injected Firestore client and collection names."""
        self._client = client
        self._records_collection = records_collection
        self._dedupe_collection = dedupe_collection

    async def write_record(self, record: SavingsRecord) -> None:
        """Write the record to Firestore off the event loop."""
        await asyncio.wait_for(
            asyncio.to_thread(self._write_sync, record), timeout=_TIMEOUT_S
        )

    async def is_duplicate_image(self, uid: str, image_hash: str) -> bool:
        """Check the dedupe collection for an existing marker."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._is_duplicate_sync, uid, image_hash),
            timeout=_TIMEOUT_S,
        )

    async def reserve_image(self, uid: str, image_hash: str) -> None:
        """Persist a dedupe marker off the event loop."""
        await asyncio.wait_for(
            asyncio.to_thread(self._reserve_sync, uid, image_hash),
            timeout=_TIMEOUT_S,
        )

    @staticmethod
    def _dedupe_key(uid: str, image_hash: str) -> str:
        """Build the composite dedupe document id."""
        return f"{uid}:{image_hash}"

    def _write_sync(self, record: SavingsRecord) -> None:
        """Blocking Firestore record write."""
        self._client.collection(self._records_collection).add(  # type: ignore[attr-defined]
            asdict(record)
        )

    def _is_duplicate_sync(self, uid: str, image_hash: str) -> bool:
        """Blocking dedupe-marker existence check."""
        doc = (
            self._client.collection(self._dedupe_collection)  # type: ignore[attr-defined]
            .document(self._dedupe_key(uid, image_hash))
            .get()
        )
        return bool(doc.exists)

    def _reserve_sync(self, uid: str, image_hash: str) -> None:
        """Blocking dedupe-marker write."""
        self._client.collection(self._dedupe_collection).document(  # type: ignore[attr-defined]
            self._dedupe_key(uid, image_hash)
        ).set({"reserved": True})
