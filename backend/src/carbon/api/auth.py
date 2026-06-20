# SPDX-License-Identifier: MIT
"""Firebase Authentication dependency.

Verifies the Firebase ID token (signature, ``aud``/``iss``, expiry) and injects
the ``uid``. Any failure yields a 401 via the error envelope. The verifier is a
Protocol so unit tests substitute a fake without touching Firebase.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from fastapi import Request
from firebase_admin import auth as firebase_auth

from carbon.api.errors import ApiError


class TokenVerifier(Protocol):
    """Port for verifying a bearer ID token and returning its claims."""

    def verify(self, token: str) -> Mapping[str, Any]:
        """Return decoded claims for ``token`` or raise on invalid tokens."""
        ...


class FirebaseTokenVerifier:
    """Verifies Firebase ID tokens via the Admin SDK."""

    def verify(self, token: str) -> Mapping[str, Any]:
        """Verify and decode a Firebase ID token.

        Raises:
            ValueError: If the token is malformed.
            firebase_admin.auth.InvalidIdTokenError: If verification fails.
        """
        claims: dict[str, Any] = firebase_auth.verify_id_token(token)
        return claims


def _extract_bearer(request: Request) -> str:
    """Pull the bearer token from the Authorization header.

    Raises:
        ApiError: 401 when the header is missing or malformed.
    """
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ApiError(401, "unauthorized", "Missing or malformed bearer token.")
    return token.strip()


def require_uid(request: Request) -> str:
    """FastAPI dependency that authenticates the caller and returns the uid.

    Raises:
        ApiError: 401 when the token is missing, malformed, or invalid.
    """
    verifier: TokenVerifier = request.app.state.deps.token_verifier
    token = _extract_bearer(request)
    try:
        claims = verifier.verify(token)
    except (ValueError, firebase_auth.InvalidIdTokenError) as exc:
        raise ApiError(401, "unauthorized", "Invalid authentication token.") from exc
    uid = claims.get("uid") or claims.get("sub")
    if not isinstance(uid, str) or not uid:
        raise ApiError(401, "unauthorized", "Token missing subject claim.")
    request.state.uid = uid
    return uid
