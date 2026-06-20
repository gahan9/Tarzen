# SPDX-License-Identifier: MIT
"""Export the API's OpenAPI schema to ``docs/openapi.json``.

Builds the app with lightweight stub dependencies (no GCP clients) so the schema
can be generated offline and committed as the source-of-truth API contract.

Usage:
    uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from carbon.api.container import Dependencies
from carbon.api.health import ReadinessProbe
from carbon.api.rate_limit import RateLimiter
from carbon.application.insights import InsightEngine
from carbon.core.config import Settings
from carbon.domain.registry import build_default_registry
from carbon.main import create_app

_OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


class _StubVerifier:
    """No-op token verifier so schema generation needs no Firebase."""

    def verify(self, token: str) -> dict[str, Any]:
        """Return a fixed claim set; never called during schema export."""
        return {"uid": "stub"}


def _stub_dependencies() -> Dependencies:
    """Assemble dependencies with no external clients."""
    return Dependencies(
        registry=build_default_registry(),
        insight_engine=InsightEngine(None, llm_enabled=False),
        token_verifier=_StubVerifier(),
        rate_limiter=RateLimiter(),
        readiness=ReadinessProbe({}),
    )


def main() -> None:
    """Generate and write the OpenAPI document."""
    settings = Settings(gcp_project_id="schema-export", _env_file=None)
    app = create_app(settings, deps=_stub_dependencies())
    schema = app.openapi()
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {_OUTPUT}")


if __name__ == "__main__":
    main()
