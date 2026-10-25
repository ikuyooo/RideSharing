"""Authentication / RBAC dependencies shared by every module's API.

Other modules import `User` (as a type) and the dependencies from here, never
from `identity.models`."""

import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings, get_settings
from app.db.session import get_db
from app.modules.identity import security, service
from app.modules.identity.models import User

__all__ = ["User", "ensure_owner_or_admin", "get_current_user", "require_roles"]

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise ApiError(401, "NOT_AUTHENTICATED", "Bearer access token required")
    try:
        claims = security.decode_access_token(credentials.credentials, settings.jwt_secret)
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise ApiError(401, "INVALID_ACCESS_TOKEN", "Access token is invalid or expired") from exc
    user = service.get_user(session, user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "INVALID_ACCESS_TOKEN", "Access token is invalid or expired")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    """The role is read from the database (not the token), so role changes and
    deactivation take effect immediately."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ApiError(403, "FORBIDDEN_ROLE", f"Requires role: {', '.join(roles)}")
        return user

    return dependency


def ensure_owner_or_admin(resource_user_id: uuid.UUID, user: User) -> None:
    """Object-level authorization (Section 59.1). Answers 404 so that other
    users' resources are not revealed to exist."""
    if user.role != "ADMIN" and resource_user_id != user.id:
        raise ApiError(404, "NOT_FOUND", "Resource not found")
