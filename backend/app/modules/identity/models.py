"""identity module tables (Revision 9, Section 54: `users`, `user_preferences`).

`users` has no column specification in Section 56.1; every column here is a
TECHNICAL ADDITION needed by authentication/RBAC (Section 59.1) and as the FK
target of 56.1 tables. `refresh_tokens` is a TECHNICAL ADDITION implementing the
revocable refresh token of Section 59.1. `user_preferences` is not created yet
(no columns specified and nothing depends on it in Phase 1).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import in_check

ROLES = ("PASSENGER", "DRIVER", "ADMIN")
# P1-D6: optional, never required at registration, never logged.
GENDERS = ("FEMALE", "MALE", "OTHER")
# P1-D6: no verification method is approved yet, so the only allowed value is
# UNVERIFIED. Self-declared gender can therefore never satisfy hard constraint #11.
GENDER_VERIFICATION_STATUSES = ("UNVERIFIED",)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(16))
    gender_verification_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="UNVERIFIED"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        in_check("role", ROLES, "role"),
        in_check("gender", GENDERS, "gender"),
        in_check("gender_verification_status", GENDER_VERIFICATION_STATUSES, "gender_verification_status"),
        Index("uq_users_email_lower", func.lower(email), unique=True),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 of the opaque token; the token itself is never stored.
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # All tokens obtained by rotating one login share a family (reuse detection).
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
