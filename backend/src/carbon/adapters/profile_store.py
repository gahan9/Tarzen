# SPDX-License-Identifier: MIT
"""Firestore-backed anonymous profiles + deterministic handle generation.

Each user maps to a stable anonymous handle (e.g. ``SwiftFox-4821``) and a coarse
region. Only the handle and region are ever exposed on leaderboards, preserving
anonymity. Handles are generated deterministically from the uid so they are
stable across sessions, then uniqueness-checked against the store so two users
never share one. The animal word lets the frontend pair the handle with a
matching emoji without storing any image asset. An in-memory implementation backs
unit tests.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import asdict, dataclass, field, replace
from typing import Protocol

from google.cloud import firestore

DEFAULT_PROFILES_COLLECTION = "profiles"
_TIMEOUT_S = 10.0
_MAX_HANDLE_ATTEMPTS = 8
_SUFFIX_MODULO = 10_000
_FALLBACK_EMOJI = "\N{PAW PRINTS}"

# License-clean, original word lists (no third-party data). Kept short to stay
# repo-lean while still yielding ample unique combinations.
_ADJECTIVES: tuple[str, ...] = (
    "Swift",
    "Brave",
    "Calm",
    "Bright",
    "Bold",
    "Gentle",
    "Keen",
    "Lively",
    "Mighty",
    "Noble",
    "Quick",
    "Sunny",
    "Clever",
    "Kind",
    "Steady",
    "Wise",
)
# Each animal pairs with a decorative emoji so the frontend can render an anchor
# without any image asset. Falls back to paw prints for any animal without an
# exact glyph.
_ANIMALS: tuple[str, ...] = (
    "Fox",
    "Otter",
    "Heron",
    "Lynx",
    "Robin",
    "Bison",
    "Wren",
    "Hare",
    "Falcon",
    "Badger",
    "Newt",
    "Stoat",
    "Finch",
    "Marten",
    "Owl",
    "Vole",
)
_ANIMAL_EMOJI: dict[str, str] = {
    "Fox": "\N{FOX FACE}",
    "Otter": "\N{OTTER}",
    "Heron": "\N{BIRD}",
    "Lynx": "\N{CAT}",
    "Robin": "\N{BIRD}",
    "Bison": "\N{BISON}",
    "Wren": "\N{BIRD}",
    "Hare": "\N{RABBIT}",
    "Falcon": "\N{EAGLE}",
    "Badger": "\N{BADGER}",
    "Newt": "\N{LIZARD}",
    "Stoat": "\N{BEAVER}",
    "Finch": "\N{BIRD}",
    "Marten": "\N{OTTER}",
    "Owl": "\N{OWL}",
    "Vole": "\N{MOUSE}",
}


@dataclass(frozen=True, slots=True)
class Profile:
    """An anonymous user profile.

    Attributes:
        uid: Authenticated user id (never exposed externally).
        anon_handle: Stable, human-friendly anonymous handle.
        emoji: Decorative emoji paired with the handle's animal.
        region: Coarse region key used for regional leaderboards.
        total_kg_co2e_saved: Lifetime avoided emissions recorded by the user.
    """

    uid: str
    anon_handle: str
    emoji: str
    region: str
    total_kg_co2e_saved: float = 0.0


def _identity_parts(seed: str, attempt: int) -> tuple[str, str]:
    """Return the ``(handle, emoji)`` derived deterministically from a seed."""
    digest = hashlib.sha256(f"{seed}:{attempt}".encode()).digest()
    adjective = _ADJECTIVES[digest[0] % len(_ADJECTIVES)]
    animal = _ANIMALS[digest[1] % len(_ANIMALS)]
    suffix = int.from_bytes(digest[2:5], "big") % _SUFFIX_MODULO
    handle = f"{adjective}{animal}-{suffix:04d}"
    emoji = _ANIMAL_EMOJI.get(animal, _FALLBACK_EMOJI)
    return handle, emoji


def emoji_for_handle(handle: str) -> str:
    """Return the decorative emoji implied by an anonymous handle's animal.

    Handles read ``<Adjective><Animal>-<NNNN>``; the animal is recovered as the
    suffix of the alphabetic part so any handle (including other users') can be
    decorated without a datastore lookup. Falls back to paw prints.
    """
    alpha = handle.split("-", 1)[0]
    for animal in _ANIMALS:
        if alpha.endswith(animal):
            return _ANIMAL_EMOJI.get(animal, _FALLBACK_EMOJI)
    return _FALLBACK_EMOJI


def generate_anon_handle(seed: str, *, attempt: int = 0) -> str:
    """Derive a deterministic anonymous handle from a seed.

    The same ``(seed, attempt)`` always yields the same handle, so a user's
    primary handle (attempt 0) is stable; higher attempts are used only to break
    a rare collision with another user.

    Args:
        seed: A stable per-user seed (the uid).
        attempt: Disambiguation counter for collision resolution.

    Returns:
        A handle of the form ``<Adjective><Animal>-<NNNN>``.
    """
    handle, _emoji = _identity_parts(seed, attempt)
    return handle


class ProfileStore(Protocol):
    """Port for anonymous profile persistence."""

    async def get(self, uid: str) -> Profile | None:
        """Return the stored profile for ``uid`` or ``None`` if absent."""
        ...

    async def get_or_create(self, uid: str, region: str) -> Profile:
        """Return the existing profile or create one with a unique handle."""
        ...

    async def add_savings(self, uid: str, kg_co2e_saved: float) -> None:
        """Increment the user's lifetime saved total (creates if needed)."""
        ...


def _resolve_identity(uid: str, taken: set[str]) -> tuple[str, str]:
    """Find the first deterministic ``(handle, emoji)`` for ``uid`` not taken."""
    for attempt in range(_MAX_HANDLE_ATTEMPTS):
        handle, emoji = _identity_parts(uid, attempt)
        if handle not in taken:
            return handle, emoji
    # Extremely unlikely; fall back to a uid-suffixed handle for guaranteed
    # uniqueness without leaking the full uid.
    handle, emoji = _identity_parts(uid, 0)
    return f"{handle}-{uid[:6]}", emoji


@dataclass(slots=True)
class InMemoryProfileStore:
    """In-memory :class:`ProfileStore` for tests and local runs."""

    profiles: dict[str, Profile] = field(default_factory=dict)

    async def get(self, uid: str) -> Profile | None:
        """Return the stored profile or ``None``."""
        return self.profiles.get(uid)

    async def get_or_create(self, uid: str, region: str) -> Profile:
        """Return the existing profile or mint one with a unique handle."""
        existing = self.profiles.get(uid)
        if existing is not None:
            return existing
        taken = {p.anon_handle for p in self.profiles.values()}
        handle, emoji = _resolve_identity(uid, taken)
        profile = Profile(uid=uid, anon_handle=handle, emoji=emoji, region=region)
        self.profiles[uid] = profile
        return profile

    async def add_savings(self, uid: str, kg_co2e_saved: float) -> None:
        """Increment the in-memory lifetime saved total for ``uid``."""
        current = await self.get_or_create(uid, "global")
        self.profiles[uid] = replace(
            current,
            total_kg_co2e_saved=current.total_kg_co2e_saved + kg_co2e_saved,
        )


class FirestoreProfileStore:
    """Firestore-backed :class:`ProfileStore` keyed by uid."""

    def __init__(
        self, client: object, *, collection: str = DEFAULT_PROFILES_COLLECTION
    ) -> None:
        """Initialise with an injected Firestore client and collection name."""
        self._client = client
        self._collection = collection

    async def get(self, uid: str) -> Profile | None:
        """Read the profile document off the event loop."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._get_sync, uid), timeout=_TIMEOUT_S
        )

    async def get_or_create(self, uid: str, region: str) -> Profile:
        """Return or create the profile, resolving handle collisions."""
        return await asyncio.wait_for(
            asyncio.to_thread(self._get_or_create_sync, uid, region),
            timeout=_TIMEOUT_S,
        )

    async def add_savings(self, uid: str, kg_co2e_saved: float) -> None:
        """Increment the user's lifetime saved total off the event loop."""
        await asyncio.wait_for(
            asyncio.to_thread(self._add_savings_sync, uid, kg_co2e_saved),
            timeout=_TIMEOUT_S,
        )

    def _get_sync(self, uid: str) -> Profile | None:
        """Blocking profile read mapped to :class:`Profile`."""
        doc = (
            self._client.collection(self._collection)  # type: ignore[attr-defined]
            .document(uid)
            .get()
        )
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        handle = str(data["anon_handle"])
        return Profile(
            uid=uid,
            anon_handle=handle,
            emoji=str(data.get("emoji", _FALLBACK_EMOJI)),
            region=str(data.get("region", "global")),
            total_kg_co2e_saved=float(data.get("total_kg_co2e_saved", 0.0)),
        )

    def _get_or_create_sync(self, uid: str, region: str) -> Profile:
        """Blocking get-or-create with handle-uniqueness resolution."""
        existing = self._get_sync(uid)
        if existing is not None:
            return existing
        for attempt in range(_MAX_HANDLE_ATTEMPTS):
            handle, emoji = _identity_parts(uid, attempt)
            if not self._handle_taken_sync(handle):
                profile = Profile(
                    uid=uid, anon_handle=handle, emoji=emoji, region=region
                )
                self._client.collection(self._collection).document(  # type: ignore[attr-defined]
                    uid
                ).set(asdict(profile))
                return profile
        fallback, emoji = _identity_parts(uid, 0)
        profile = Profile(
            uid=uid,
            anon_handle=f"{fallback}-{uid[:6]}",
            emoji=emoji,
            region=region,
        )
        self._client.collection(self._collection).document(uid).set(  # type: ignore[attr-defined]
            asdict(profile)
        )
        return profile

    def _add_savings_sync(self, uid: str, kg_co2e_saved: float) -> None:
        """Blocking atomic increment of the lifetime saved total.

        The profile document is created first if absent, then the total is
        bumped with a server-side :class:`~google.cloud.firestore.Increment`
        so concurrent writes accumulate without a lost-update race (no
        read-modify-write window).
        """
        self._get_or_create_sync(uid, "global")
        self._client.collection(self._collection).document(uid).update(  # type: ignore[attr-defined]
            {"total_kg_co2e_saved": firestore.Increment(kg_co2e_saved)}
        )

    def _handle_taken_sync(self, handle: str) -> bool:
        """Return whether any profile already uses ``handle``."""
        query = (
            self._client.collection(self._collection)  # type: ignore[attr-defined]
            .where("anon_handle", "==", handle)
            .limit(1)
            .get()
        )
        return len(list(query)) > 0
