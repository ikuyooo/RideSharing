"""P1.3 - identity: registration, Argon2id, access/refresh tokens, RBAC,
object-level authorization, gender privacy (P1-D6)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.api_helpers import PASSWORD, auth, client, login, new_admin, new_user, register  # noqa: F401

pytestmark = pytest.mark.db


def test_register_hashes_password_with_argon2id(client: TestClient, db_session: Session) -> None:
    user = register(client)
    stored = db_session.execute(text("SELECT password_hash FROM users WHERE id = :i"), {"i": user["id"]}).scalar_one()
    assert stored.startswith("$argon2id$")
    assert PASSWORD not in stored
    assert "password" not in user and "password_hash" not in user


def test_register_rejects_admin_role_and_duplicate_email(client: TestClient) -> None:
    resp = client.post("/api/auth/register", json={"email": "a@example.com", "password": PASSWORD, "role": "ADMIN"})
    assert resp.status_code == 422
    register(client, email="dup@example.com")
    resp = client.post("/api/auth/register", json={"email": "DUP@example.com", "password": PASSWORD, "role": "PASSENGER"})
    assert resp.status_code == 409 and resp.json()["error"]["code"] == "EMAIL_TAKEN"


def test_login_failure_is_generic(client: TestClient) -> None:
    user = register(client)
    wrong_pw = client.post("/api/auth/login", json={"email": user["email"], "password": "wrong-password"})
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()


def test_access_token_lifetime_is_15_minutes(client: TestClient) -> None:
    user = register(client)
    tokens = login(client, user["email"])
    claims = jwt.decode(tokens["access_token"], options={"verify_signature": False})
    assert claims["exp"] - claims["iat"] == 15 * 60
    assert claims["typ"] == "access"


def test_me_requires_valid_token(client: TestClient) -> None:
    assert client.get("/api/users/me").json()["error"]["code"] == "NOT_AUTHENTICATED"
    resp = client.get("/api/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401
    from app.core.settings import get_settings

    expired = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000000", "typ": "access",
         "exp": datetime.now(UTC) - timedelta(seconds=1)},
        get_settings().jwt_secret, algorithm="HS256",
    )
    assert client.get("/api/users/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    forged = jwt.encode({"sub": "x", "typ": "access", "exp": datetime.now(UTC) + timedelta(minutes=5)},
                        "another-secret", algorithm="HS256")
    assert client.get("/api/users/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_refresh_rotates_and_detects_reuse(client: TestClient) -> None:
    user = register(client)
    first = login(client, user["email"])
    second = client.post("/api/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    second = second.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get("/api/users/me", headers=auth(second)).status_code == 200

    # Re-using the rotated (revoked) token revokes the whole family.
    reuse = client.post("/api/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reuse.status_code == 401 and reuse.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"
    after = client.post("/api/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert after.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    user = register(client)
    tokens = login(client, user["email"])
    assert client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_expired_refresh_token_rejected(client: TestClient, db_session: Session) -> None:
    user = register(client)
    tokens = login(client, user["email"])
    db_session.execute(text("UPDATE refresh_tokens SET expires_at = now() - interval '1 second'"))
    db_session.commit()
    resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401 and resp.json()["error"]["code"] == "REFRESH_TOKEN_EXPIRED"


def test_deactivated_user_loses_access(client: TestClient, db_session: Session) -> None:
    user, headers = new_user(client)
    db_session.execute(text("UPDATE users SET is_active = false WHERE id = :i"), {"i": user["id"]})
    db_session.commit()
    assert client.get("/api/users/me", headers=headers).status_code == 401


def test_rbac_role_checks(client: TestClient, db_session: Session) -> None:
    _, passenger = new_user(client, "PASSENGER")
    _, driver = new_user(client, "DRIVER")
    _, admin = new_admin(client, db_session)
    assert client.get("/api/driver/profile", headers=passenger).json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert client.get("/api/driver/profile", headers=admin).status_code == 403
    assert client.get("/api/driver/profile", headers=driver).status_code == 200
    review = client.post("/api/admin/drivers/00000000-0000-0000-0000-000000000000/kyc-review",
                         json={"decision": "VERIFIED"}, headers=driver)
    assert review.status_code == 403


def test_gender_is_optional_self_declared_and_never_verified(client: TestClient, db_session: Session) -> None:
    user, headers = new_user(client)
    assert user["gender"] is None and user["gender_verification_status"] == "UNVERIFIED"
    resp = client.put("/api/users/me/gender", json={"gender": "FEMALE"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["gender"] == "FEMALE"
    assert resp.json()["gender_verification_status"] == "UNVERIFIED"
    # The API offers no way to send a verification status.
    resp = client.put("/api/users/me/gender", json={"gender": "MALE", "gender_verification_status": "VERIFIED"},
                      headers=headers)
    assert resp.json()["gender_verification_status"] == "UNVERIFIED"
