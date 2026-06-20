# SPDX-License-Identifier: MIT
"""API error types and exception handlers mapping to the wire envelope.

Every failure leaves the service as ``{"error": {code, message, request_id}}``
with an appropriate HTTP status. Internal details are never leaked.
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from carbon.domain.errors import DomainError, UnsupportedDomainError
from carbon.models.schemas import ErrorDetail, ErrorEnvelope

_LOGGER = logging.getLogger(__name__)


class ApiError(Exception):
    """An API-layer error with an explicit HTTP status and stable code.

    Attributes:
        status_code: HTTP status to return.
        code: Stable machine-readable error code.
        message: Safe, human-readable description.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _request_id(request: Request) -> str:
    """Return the correlation id stashed on the request, if any."""
    return str(getattr(request.state, "request_id", "unknown"))


def _envelope(code: str, message: str, request_id: str, status: int) -> JSONResponse:
    """Build a JSON error-envelope response."""
    body = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message, request_id=request_id)
    )
    return JSONResponse(status_code=status, content=body.model_dump())


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """Map an :class:`ApiError` to the envelope."""
    return _envelope(exc.code, exc.message, _request_id(request), exc.status_code)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Map a :class:`DomainError` to a 400/404 envelope."""
    status = 404 if isinstance(exc, UnsupportedDomainError) else 400
    return _envelope(exc.code, exc.message, _request_id(request), status)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map request-validation failures to a 422 envelope."""
    return _envelope(
        "validation_error",
        "Request failed validation.",
        _request_id(request),
        422,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map any unhandled exception to a 500 envelope without leaking details."""
    _LOGGER.exception("unhandled_error", extra={"request_id": _request_id(request)})
    return _envelope(
        "internal_error",
        "An unexpected error occurred.",
        _request_id(request),
        500,
    )
