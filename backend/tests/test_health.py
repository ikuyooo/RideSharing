"""Health endpoints. Dependencies point at closed ports, so readiness must be 503."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@127.0.0.1:1/db")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    monkeypatch.setenv("OSRM_CAR_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("OSRM_MOTORBIKE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("CONFIG_BASELINE_PATH", str(REPO_ROOT / "config" / "mvp_config_baseline_v1.yaml"))
    monkeypatch.setenv("DEPENDENCY_TIMEOUT_S", "1")

    from app.core.settings import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    return TestClient(create_app())


def test_live_ok(client: TestClient) -> None:
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_reports_unreachable_dependencies(client: TestClient) -> None:
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["config_baseline_version"] == "MVP_CONFIG_BASELINE_V1"
    assert body["checks"]["config_baseline"]["status"] == "ok"
    for name in ("postgres", "redis", "osrm_car", "osrm_motorbike"):
        assert body["checks"][name]["status"] == "error", name
