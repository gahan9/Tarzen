# SPDX-License-Identifier: MIT
"""Structured JSON logging configuration.

Emits one JSON object per log record so Cloud Logging can index fields. Only
explicitly allow-listed ``extra`` fields are serialized; request/response bodies
are never logged, keeping PII and secrets out of logs.
"""

from __future__ import annotations

import json
import logging
from typing import Any

# Fields that may be attached via ``logger.*(..., extra={...})`` and surfaced.
_ALLOWED_EXTRA: frozenset[str] = frozenset(
    {
        "request_id",
        "trace_id",
        "uid",
        "route",
        "method",
        "status",
        "latency_ms",
        "llm_used",
        "gemini_latency_ms",
        "error_type",
        "attempt",
        "event",
    }
)


class JsonFormatter(logging.Formatter):
    """Render a log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize the record to JSON with allow-listed extra fields."""
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _ALLOWED_EXTRA:
            if key in record.__dict__:
                payload[key] = record.__dict__[key]
        if record.exc_info:
            payload["exc_type"] = getattr(record.exc_info[0], "__name__", "error")
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger.

    Args:
        level: Root log level name (e.g. ``INFO``).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
