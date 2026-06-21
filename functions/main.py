# SPDX-License-Identifier: MIT
"""Cloud Functions (gen2) entry module for the footprint aggregation consumer.

Deploy shim (uncommitted; generated for live deploy): the Functions Framework
imports ``main`` by default, so this exposes the CloudEvent entry point and
delegates to the roadmap stub in ``aggregate_consumer``.

The stub raises ``NotImplementedError`` (Phase 7 not yet landed). To guarantee a
single delivery can never become a poison-message retry storm, this wrapper
catches that specific signal, logs a warning, and returns normally so Pub/Sub
acks the message. Any *other* exception is allowed to propagate.
"""

from __future__ import annotations

import logging
from typing import Any

import functions_framework

from aggregate_consumer import handle_footprint_event as _impl

_LOGGER = logging.getLogger(__name__)


@functions_framework.cloud_event
def handle_footprint_event(cloud_event: Any) -> None:
    """CloudEvent entry point; no-ops (acks) while the consumer is a stub."""
    try:
        _impl(cloud_event)
    except NotImplementedError:
        _LOGGER.warning(
            "aggregate_consumer stub: acking event without processing "
            "(Phase 7 not yet implemented)"
        )
