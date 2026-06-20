# SPDX-License-Identifier: MIT
"""Typed domain errors.

Domain errors carry a stable machine-readable ``code`` so the API layer can map
them to the wire error envelope without leaking internal details.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for recoverable domain-level failures.

    Attributes:
        code: Stable, machine-readable error code surfaced to clients.
        message: Safe, human-readable description (never contains secrets/PII).
    """

    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnsupportedDomainError(DomainError):
    """Raised when no tracker is registered for the requested domain."""

    code = "unsupported_domain"


class UnsupportedModeError(DomainError):
    """Raised when a tracker receives a mode it does not recognise."""

    code = "unsupported_mode"


class InvalidInputError(DomainError):
    """Raised when calculation inputs are structurally invalid."""

    code = "invalid_input"
