import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Self-registration is limited to these roles; ADMIN accounts are created with
# the identity CLI only.
SelfServiceRole = Literal["PASSENGER", "DRIVER"]


class RegisterIn(BaseModel):
    email: EmailStr
    # Revision 9 does not specify a password policy; 8+ characters is a technical default.
    password: str = Field(min_length=8, max_length=128)
    role: SelfServiceRole
    display_name: str | None = Field(default=None, max_length=100)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=256)


class TokenPair(BaseModel):
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str
    refresh_token_expires_at: datetime
    token_type: Literal["bearer"] = "bearer"


class UserOut(BaseModel):
    """Only ever returned to the user themself (GET /api/users/me)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    display_name: str | None
    gender: str | None
    gender_verification_status: str
    created_at: datetime


class GenderIn(BaseModel):
    """P1-D6: optional self-declaration; never treated as verified."""

    gender: Literal["FEMALE", "MALE", "OTHER"] | None
