# SPDX-License-Identifier: MIT
# syntax=docker/dockerfile:1

# Pinned slim base for reproducible, minimal images.
FROM python:3.11.9-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_PORT=8080

WORKDIR /app

# Install the package (and its pinned-minimum deps) from source.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

# Drop privileges: never run as root.
USER appuser

EXPOSE 8080

# Cloud Run sets $PORT; default to 8080 locally.
CMD ["sh", "-c", "uvicorn carbon.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8080}"]
