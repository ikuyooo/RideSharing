"""Credential primitives (Revision 9, Section 59.1): Argon2id password hashing,
short-lived JWT access tokens, opaque revocable refresh tokens."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# argon2-cffi's PasswordHasher uses the Argon2id variant by default.
_hasher = PasswordHasher()
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def issue_access_token(user_id: uuid.UUID, role: str, secret: str, ttl_s: int) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires = now + timedelta(seconds=ttl_s)
    claims = {
        "sub": str(user_id),
        "role": role,
        "typ": "access",
        "iat": now,
        "exp": expires,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, secret, algorithm=_ALGORITHM), expires


def decode_access_token(token: str, secret: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError on any invalid, expired or non-access token."""
    claims = jwt.decode(token, secret, algorithms=[_ALGORITHM], options={"require": ["sub", "exp", "typ"]})
    if claims.get("typ") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return claims


def new_refresh_token() -> tuple[str, str]:
    """Returns (opaque token for the client, SHA-256 hex digest to store)."""
    token = secrets.token_urlsafe(48)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
