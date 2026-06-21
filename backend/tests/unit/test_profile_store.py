# SPDX-License-Identifier: MIT
"""Tests for anonymous profiles: handles, emoji, totals, and Firestore."""

from __future__ import annotations

from carbon.adapters.profile_store import (
    FirestoreProfileStore,
    InMemoryProfileStore,
    emoji_for_handle,
    generate_anon_handle,
)
from tests.unit.test_savings_store import RichFakeFirestore


def test_handle_generation_is_deterministic() -> None:
    """The same uid always yields the same primary handle."""
    assert generate_anon_handle("uid-1") == generate_anon_handle("uid-1")
    assert generate_anon_handle("uid-1", attempt=1) != generate_anon_handle("uid-1")


def test_emoji_for_handle_recovers_animal() -> None:
    """A handle's emoji is derived from its embedded animal, with a fallback."""
    assert emoji_for_handle("SwiftFox-0001") == "\N{FOX FACE}"
    assert emoji_for_handle("NoMatchHere-0001") == "\N{PAW PRINTS}"


async def test_in_memory_get_or_create_is_stable_and_unique() -> None:
    """get_or_create is idempotent per uid and assigns an emoji."""
    store = InMemoryProfileStore()

    first = await store.get_or_create("uid-1", "GB")
    again = await store.get_or_create("uid-1", "GB")

    assert first == again
    assert first.region == "GB"
    assert first.emoji


async def test_in_memory_add_savings_accumulates() -> None:
    """add_savings increments the lifetime total for a user."""
    store = InMemoryProfileStore()
    await store.get_or_create("uid-1", "GB")

    await store.add_savings("uid-1", 1.5)
    await store.add_savings("uid-1", 2.0)

    profile = await store.get("uid-1")
    assert profile is not None
    assert profile.total_kg_co2e_saved == 3.5


async def test_firestore_profile_roundtrip_and_total() -> None:
    """Firestore store creates a profile and persists the saved total."""
    store = FirestoreProfileStore(RichFakeFirestore())

    created = await store.get_or_create("uid-1", "US")
    assert created.emoji
    assert (await store.get("uid-1")) == created

    await store.add_savings("uid-1", 4.25)
    updated = await store.get("uid-1")
    assert updated is not None
    assert updated.total_kg_co2e_saved == 4.25


async def test_firestore_handle_uniqueness_resolves_collision() -> None:
    """A taken primary handle forces a different handle for a new user."""
    fake = RichFakeFirestore()
    store = FirestoreProfileStore(fake)

    # Pre-seed the primary handle for uid-1 as belonging to someone else.
    primary = generate_anon_handle("uid-1")
    fake.collection("profiles").document("other").set(
        {"anon_handle": primary, "emoji": "x", "region": "GB"}
    )

    created = await store.get_or_create("uid-1", "GB")

    assert created.anon_handle != primary
