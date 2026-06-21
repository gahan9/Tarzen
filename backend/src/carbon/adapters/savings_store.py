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

from google.api_core.exceptions import AlreadyExists

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

    async def try_reserve_image(self, uid: str, image_hash: str) -> bool:
        """Atomically claim an image hash for ``uid``.

        Returns ``True`` when the hash was newly reserved and ``False`` when it
        was already present. Implementations MUST perform the check-and-insert
        atomically so two concurrent identical uploads cannot both succeed
        (no check-then-act TOCTOU window).
        """
        ...


@dataclass(slots=True)
class InMemorySavingsStore:
    """In-memory :class:`SavingsStore` for tests and local runs."""

    records: list[SavingsRecord] = field(default_factory=list)
    seen_hashes: set[tuple[str, str]] = field(default_factory=set)

    async def write_record(self, record: SavingsRecord) -> None:
        """Append the record to the in-memory list."""
        self.records.append(record)

    async def try_reserve_image(self, uid: str, image_hash: str) -> bool:
        """Claim ``(uid, image_hash)`` via an atomic set-membership delta."""
        key = (uid, image_hash)
        if key in self.seen_hashes:
            return False
        self.seen_hashes.add(key)
        return True


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

    async def try_reserve_image(self, uid: str, image_hash: str) -> bool:
        """Atomically reserve a dedupe marker off the event loop."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._try_reserve_sync, uid, image_hash),
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

    def _try_reserve_sync(self, uid: str, image_hash: str) -> bool:
        """Blocking atomic dedupe-marker create.

        ``create`` writes the document only if it does not already exist,
        raising :class:`AlreadyExists` otherwise. This closes the
        check-then-act race two concurrent identical uploads would expose.
        """
        doc = self._client.collection(self._dedupe_collection).document(  # type: ignore[attr-defined]
            self._dedupe_key(uid, image_hash)
        )
        try:
            doc.create({"reserved": True})
        except AlreadyExists:
            return False
        return True
