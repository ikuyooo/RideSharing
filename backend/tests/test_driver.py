"""P1.4 - driver profile, vehicles, settings, location and the KYC mock
(Revision 9 Sections 3, 56.1, 57, 81)."""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.api_helpers import client, new_admin, new_user  # noqa: F401

pytestmark = pytest.mark.db


def _vehicle(client: TestClient, headers: dict, vehicle_type: str = "CAR4", plate: str = "29A-12345") -> dict:
    resp = client.post("/api/driver/vehicles", json={"vehicle_type": vehicle_type, "license_plate": plate}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _submit(client: TestClient, headers: dict) -> dict:
    resp = client.post(
        "/api/driver/kyc/submit",
        json={"driving_licence_number": "0123456789", "driving_licence_class": "B2",
              "vehicle_registration_number": "REG-0001"},
        headers=headers,
    )
    return resp


def test_vehicle_capacity_comes_from_baseline(client: TestClient) -> None:
    _, headers = new_user(client, "DRIVER")
    assert _vehicle(client, headers, "BIKE", "29B1-00001")["capacity"] == 1
    assert _vehicle(client, headers, "CAR4", "30A-00002")["capacity"] == 4
    dup = client.post("/api/driver/vehicles", json={"vehicle_type": "CAR4", "license_plate": "30a-00002"}, headers=headers)
    assert dup.status_code == 409


def test_pool_and_intercity_locked_until_kyc_verified(client: TestClient, db_session: Session) -> None:
    driver, headers = new_user(client, "DRIVER")
    _vehicle(client, headers)
    profile = client.get("/api/driver/profile", headers=headers).json()
    assert profile["kyc_status"] == "NONE"

    # CAR_URBAN_PRIVATE stays available without KYC (Section 81 step 2).
    assert client.put("/api/driver/settings", json={"accepts_urban": True}, headers=headers).status_code == 200
    for flag in ("pool_enabled", "accepts_intercity"):
        resp = client.put("/api/driver/settings", json={flag: True}, headers=headers)
        assert resp.status_code == 403 and resp.json()["error"]["code"] == "KYC_REQUIRED"

    assert _submit(client, headers).json()["kyc_status"] == "PENDING"
    assert _submit(client, headers).status_code == 409  # already pending
    assert client.put("/api/driver/settings", json={"pool_enabled": True}, headers=headers).status_code == 403

    _, admin = new_admin(client, db_session)
    review = client.post(f"/api/admin/drivers/{driver['id']}/kyc-review", json={"decision": "VERIFIED"}, headers=admin)
    assert review.status_code == 200 and review.json()["kyc_status"] == "VERIFIED"
    resp = client.put("/api/driver/settings", json={"pool_enabled": True, "accepts_intercity": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["pool_enabled"] and resp.json()["accepts_intercity"]


def test_rejected_kyc_can_resubmit_and_review_needs_pending(client: TestClient, db_session: Session) -> None:
    driver, headers = new_user(client, "DRIVER")
    _, admin = new_admin(client, db_session)
    url = f"/api/admin/drivers/{driver['id']}/kyc-review"
    assert client.post(url, json={"decision": "VERIFIED"}, headers=admin).status_code == 404  # no profile yet
    client.get("/api/driver/profile", headers=headers)
    assert client.post(url, json={"decision": "VERIFIED"}, headers=admin).json()["error"]["code"] == "KYC_NOT_PENDING"
    _submit(client, headers)
    assert client.post(url, json={"decision": "REJECTED"}, headers=admin).json()["kyc_status"] == "REJECTED"
    assert _submit(client, headers).json()["kyc_status"] == "PENDING"


def test_pool_requires_car4_vehicle(client: TestClient, db_session: Session) -> None:
    driver, headers = new_user(client, "DRIVER")
    _vehicle(client, headers, "BIKE", "29B1-99999")
    _submit(client, headers)
    _, admin = new_admin(client, db_session)
    client.post(f"/api/admin/drivers/{driver['id']}/kyc-review", json={"decision": "VERIFIED"}, headers=admin)
    resp = client.put("/api/driver/settings", json={"pool_enabled": True}, headers=headers)
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "CAR4_VEHICLE_REQUIRED"


def test_settings_validation(client: TestClient) -> None:
    _, headers = new_user(client, "DRIVER")
    assert client.put("/api/driver/settings", json={"max_additional_pickups": 4}, headers=headers).status_code == 422
    assert client.put("/api/driver/settings", json={"max_driver_detour_km": -1}, headers=headers).status_code == 422
    ok = client.put("/api/driver/settings", json={"max_additional_pickups": 3, "max_driver_detour_km": 2.5},
                    headers=headers)
    assert ok.status_code == 200 and ok.json()["max_additional_pickups"] == 3


def test_location_upsert_is_stored_and_not_logged(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    driver, headers = new_user(client, "DRIVER")
    caplog.set_level(logging.DEBUG)
    for lat, lon in ((21.028511, 105.854167), (21.030012, 105.850001)):
        assert client.put("/api/driver/location", json={"lat": lat, "lon": lon}, headers=headers).status_code == 204
    row = db_session.execute(
        text("SELECT ST_X(geom) AS lon, ST_Y(geom) AS lat FROM driver_locations WHERE driver_id = :d"),
        {"d": driver["id"]},
    ).one()
    assert (round(row.lat, 6), round(row.lon, 6)) == (21.030012, 105.850001)
    assert "21.0300" not in caplog.text and "105.8500" not in caplog.text
    assert client.put("/api/driver/location", json={"lat": 91, "lon": 0}, headers=headers).status_code == 422
