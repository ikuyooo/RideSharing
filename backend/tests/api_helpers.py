"""Helpers for API tests (register/login users through the real endpoints)."""

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

PASSWORD = "correct horse battery"


@pytest.fixture()
def client(app_env: None, db_session: Session) -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


def register(client: TestClient, role: str = "PASSENGER", email: str | None = None) -> dict:
    email = email or f"{role.lower()}-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "role": role})
    assert resp.status_code == 201, resp.text
    return resp.json() | {"email": email}


def login(client: TestClient, email: str, password: str = PASSWORD) -> dict:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def new_user(client: TestClient, role: str = "PASSENGER") -> tuple[dict, dict[str, str]]:
    user = register(client, role)
    return user, auth(login(client, user["email"]))


def new_admin(client: TestClient, session: Session) -> tuple[dict, dict[str, str]]:
    from app.modules.identity import service

    email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    service.create_admin(session, email, PASSWORD)
    session.execute(text("SELECT 1"))
    return {"email": email}, auth(login(client, email))
