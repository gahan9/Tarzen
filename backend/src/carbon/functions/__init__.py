# SPDX-License-Identifier: MIT
"""Event-driven Cloud Functions consumers (Phase 7).

These modules host out-of-band processors triggered by Pub/Sub. They depend only
on the domain ports/adapters, so the same logic runs locally against in-memory
fakes in unit tests and against GCP services in production.
"""

from __future__ import annotations
