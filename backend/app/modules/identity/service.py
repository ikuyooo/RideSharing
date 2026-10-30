"""identity service - the only code that reads or writes `users` and
`refresh_tokens`. Other modules call the functions below."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings
from app.modules.identity import security
from app.modules.identity.models import RefreshToken, User
from app.modules.identity.schemas import TokenPair


def get_user(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def register(session: Session, email: str, password: str, role: str, display_name: str | None) -> User:
    user = User(
        email=email,
        password_hash=security.hash_password(password),
        role=role,
        display_name=display_name,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if "uq_users_email_lower" in str(exc.orig):
            raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists") from exc
        raise
    return user


def create_admin(session: Session, email: str, password: str) -> User:
    user = User(email=email, password_hash=security.hash_password(password), role="ADMIN")
    session.add(user)
    session.commit()
    return user


def _issue_pair(session: Session, user: User, settings: Settings, family_id: uuid.UUID) -> TokenPair:
    access, access_exp = security.issue_access_token(
        user.id, user.role, settings.jwt_secret, settings.access_token_ttl_s
    )
    refresh, refresh_hash = security.new_refresh_token()
    refresh_exp = datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_s)
    session.add(RefreshToken(user_id=user.id, token_hash=refresh_hash, family_id=family_id, expires_at=refresh_exp))
    return TokenPair(
        access_token=access,
        access_token_expires_at=access_exp,
        refresh_token=refresh,
        refresh_token_expires_at=refresh_exp,
    )


def login(session: Session, email: str, password: str, settings: Settings) -> TokenPair:
    user = session.scalars(select(User).where(func.lower(User.email) == email.lower())).one_or_none()
    # Same error for unknown email and wrong password (no account enumeration).
    if user is None or not user.is_active or not security.verify_password(user.password_hash, password):
        raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password")
    pair = _issue_pair(session, user, settings, family_id=uuid.uuid4())
    session.commit()
    return pair


def _revoke_family(session: Session, family_id: uuid.UUID) -> None:
    session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )


def refresh(session: Session, refresh_token: str, settings: Settings) -> TokenPair:
    """Rotate a refresh token. Presenting an already-revoked token is treated as
    theft: the whole token family is revoked."""
    token_hash = security.hash_refresh_token(refresh_token)
    stored = session.scalars(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
    ).one_or_none()
    if stored is None:
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Refresh token is not valid")
    if stored.revoked_at is not None:
        _revoke_family(session, stored.family_id)
        session.commit()
        raise ApiError(401, "REFRESH_TOKEN_REUSED", "Refresh token was already used; please log in again")
    if stored.expires_at <= datetime.now(UTC):
        raise ApiError(401, "REFRESH_TOKEN_EXPIRED", "Refresh token has expired")
    user = session.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "INVALID_REFRESH_TOKEN", "Refresh token is not valid")

    stored.revoked_at = datetime.now(UTC)
    pair = _issue_pair(session, user, settings, family_id=stored.family_id)
    session.commit()
    return pair


def logout(session: Session, refresh_token: str) -> None:
    stored = session.scalars(
        select(RefreshToken).where(RefreshToken.token_hash == security.hash_refresh_token(refresh_token))
    ).one_or_none()
    if stored is not None:
        _revoke_family(session, stored.family_id)
        session.commit()


def set_own_gender(session: Session, user: User, gender: str | None) -> User:
    """P1-D6: self-declared and optional. Verification status stays UNVERIFIED
    (the database allows no other value until a verification method is approved)."""
    user.gender = gender
    user.gender_verification_status = "UNVERIFIED"
    session.commit()
    return user


def verified_genders(session: Session, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str | None]:
    """Hard constraint 11 reads only a VERIFIED gender; self-declared gender never counts
    (P1-D6). With no verification method approved yet every value is None."""
    rows = session.execute(select(User.id, User.gender, User.gender_verification_status)
                           .where(User.id.in_(user_ids))).tuples().all() if user_ids else []
    return {uid: (gender if status == "VERIFIED" else None) for uid, gender, status in rows}
