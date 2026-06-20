# SPDX-License-Identifier: MIT
"""Unit tests for :mod:`carbon.core.config`."""

from __future__ import annotations

import pytest

from carbon.core.config import Settings

_OPTIONAL_VARS = (
    "VERTEX_REGION",
    "GEMINI_MODEL_ID",
    "APP_LOG_LEVEL",
    "APP_PORT",
    "CORS_ALLOWED_ORIGINS",
    "SERVICE_ACCOUNT_KEY",
)


def test_settings_defaults_load_with_required_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defaults apply for every optional field when only the required env is set."""
    monkeypatch.setenv("GCP_PROJECT_ID", "demo-project")
    for var in _OPTIONAL_VARS:
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.gcp_project_id == "demo-project"
    assert settings.vertex_region == "us-central1"
    assert settings.gemini_model_id == "gemini-1.5-flash"
    assert settings.app_log_level == "INFO"
    assert settings.app_port == 8080
    assert settings.cors_allowed_origins == ["http://localhost:5173"]
    assert settings.service_account_key is None


def test_settings_env_override_is_respected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment values override defaults, including list and secret fields."""
    monkeypatch.setenv("GCP_PROJECT_ID", "prod-project")
    monkeypatch.setenv("VERTEX_REGION", "europe-west4")
    monkeypatch.setenv("GEMINI_MODEL_ID", "gemini-1.5-pro")
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_PORT", "9090")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://app.example.com, https://admin.example.com",
    )

    settings = Settings(_env_file=None)

    assert settings.gcp_project_id == "prod-project"
    assert settings.vertex_region == "europe-west4"
    assert settings.gemini_model_id == "gemini-1.5-pro"
    assert settings.app_log_level == "DEBUG"
    assert settings.app_port == 9090
    assert settings.cors_allowed_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
