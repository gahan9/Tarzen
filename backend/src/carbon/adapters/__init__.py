# SPDX-License-Identifier: MIT
"""Adapter layer: concrete implementations of domain/application ports.

Each adapter wraps an external system (Vertex AI, Firestore, BigQuery, Pub/Sub)
behind a Protocol so the core stays testable and the dependency is mockable.
"""

from __future__ import annotations
