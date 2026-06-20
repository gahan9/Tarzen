# SPDX-License-Identifier: MIT
"""Typed application settings backed by environment variables.

Settings fail fast on missing required configuration so misconfiguration
surfaces at startup, not at first request. Secrets are wrapped in
``SecretStr`` to keep them out of logs and serialized output; unwrap only at
the I/O boundary that needs the raw value.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from the environment.

    Attributes:
        gcp_project_id: Google Cloud project hosting the platform. Required.
        vertex_region: Vertex AI region used for Gemini requests.
        gemini_model_id: Vertex AI Gemini model identifier.
        app_log_level: Root logging level (e.g. ``INFO``, ``DEBUG``).
        app_port: TCP port the API server binds to.
        cors_allowed_origins: Exact origins permitted by CORS (never ``*``).
        service_account_key: Optional service-account JSON, kept secret. Models
            the secret-handling pattern; unused by the MVP which relies on
            Application Default Credentials.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    gcp_project_id: str = Field(min_length=1)
    vertex_region: str = Field(default="us-central1", min_length=1)
    gemini_model_id: str = Field(default="gemini-1.5-flash", min_length=1)
    app_log_level: str = Field(default="INFO", min_length=1)
    app_port: int = Field(default=8080, ge=1, le=65535)
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    service_account_key: SecretStr | None = Field(default=None)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string for CORS origins from env vars."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached settings instance.

    Raises:
        pydantic.ValidationError: If required environment variables are
            missing or any value fails validation.
    """
    return Settings()
