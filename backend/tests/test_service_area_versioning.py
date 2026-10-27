"""Service-area versioning (P1-D1 / P1-D3): deterministic version id, stable
re-import (ST_Equals), refusal of a changed geometry under an existing version,
and refusal to classify against RETIRED / unapproved versions.

Geometry here is SYNTHETIC (unit squares in a throwaway schema of the test
database); it exercises the pipeline mechanics, not any real boundary."""

import pytest
from sqlalchemy import Engine, text

from app.modules.trip import service_area_build as sab

pytestmark = pytest.mark.db


def _build(rules: dict | None = None) -> sab.Build:
    return sab.Build(manifest={"bbox": "105,20,106,21", "source_md5": "x"}, rules=rules or {"rules_id": "r"},
                     max_km=150.0, bbox=(105.0, 20.0, 106.0, 21.0))


def test_version_is_deterministic_and_input_sensitive() -> None:
    v1 = sab.compute_version(_build(), [1, 2], [], [1, 2, 3], 7)
    assert v1 == sab.compute_version(_build(), [1, 2], [], [1, 2, 3], 7)
    assert v1.startswith("sa-cand-") and len(v1) == len("sa-cand-") + 12
    assert v1 != sab.compute_version(_build(), [1], [], [1, 2, 3], 7)                    # urban units
    assert v1 != sab.compute_version(_build(), [1, 2], ["way/9"], [1, 2, 3], 7)          # U3 areas
    assert v1 != sab.compute_version(_build(), [1, 2], [], [1, 2, 3], 8)                 # anchor
    assert v1 != sab.compute_version(_build({"rules_id": "other"}), [1, 2], [], [1, 2, 3], 7)  # rules


@pytest.fixture()
def synthetic_units(db_engine: Engine):  # type: ignore[no-untyped-def]
    with db_engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {sab.SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {sab.SCHEMA}"))
        conn.execute(text(f"""CREATE TABLE {sab.SCHEMA}.units (osm_id bigint PRIMARY KEY, admin_level int,
            name text, iso text, input_valid boolean, geom geometry(MultiPolygon, 4326))"""))
        conn.execute(text(f"""INSERT INTO {sab.SCHEMA}.units VALUES
            (1, 6, 'A', NULL, true, ST_Multi(ST_MakeEnvelope(105.0, 20.0, 105.1, 20.1, 4326))),
            (2, 6, 'B', NULL, true, ST_Multi(ST_MakeEnvelope(105.1, 20.0, 105.2, 20.1, 4326))),
            (3, 6, 'C', NULL, true, ST_Multi(ST_MakeEnvelope(105.5, 20.5, 105.6, 20.6, 4326)))"""))
    yield
    with db_engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {sab.SCHEMA} CASCADE"))
        conn.execute(text("DELETE FROM service_areas WHERE service_area_version LIKE 'test-%'"))


def test_persist_is_stable_and_refuses_changed_geometry(db_engine: Engine, synthetic_units: None) -> None:
    sql = sab.geometry_sql("units")
    with db_engine.begin() as conn:
        assert sab.persist(conn, "test-v1", "TOTAL", sql, {"ids": [1, 2]}, {}) == "inserted"
        assert sab.persist(conn, "test-v1", "TOTAL", sql, {"ids": [1, 2]}, {}) == "unchanged (ST_Equals)"
        status, parts = conn.execute(text("SELECT status, ST_NumGeometries(geom) FROM service_areas "
                                          "WHERE service_area_version = 'test-v1'")).one()
        assert status == "CANDIDATE" and parts == 1  # adjacent squares merge into one component
    with db_engine.begin() as conn, pytest.raises(SystemExit, match="not stable"):
        sab.persist(conn, "test-v1", "TOTAL", sql, {"ids": [1, 3]}, {})


@pytest.mark.parametrize("status,allow,code", [
    ("RETIRED", True, "SERVICE_AREA_NOT_CONFIGURED"),
    ("CANDIDATE", False, "SERVICE_AREA_NOT_APPROVED"),
])
def test_classification_refuses_retired_or_unapproved(db_engine: Engine, monkeypatch: pytest.MonkeyPatch,
                                                      status: str, allow: bool, code: str) -> None:
    from sqlalchemy.orm import Session

    from app.core.errors import ApiError
    from app.core.settings import Settings
    from app.modules.trip.service import active_service_areas

    with db_engine.begin() as conn:
        for area in ("URBAN", "TOTAL"):
            conn.execute(text("INSERT INTO service_areas (area_type, service_area_version, status, geom, source_json) "
                              "VALUES (:a, 'test-gate', :s, ST_Multi(ST_MakeEnvelope(105, 20, 106, 21, 4326)), '{}')"),
                         {"a": area, "s": status})
    try:
        settings = Settings(database_url="x", redis_url="x", osrm_car_url="x", osrm_motorbike_url="x",
                            config_baseline_path="x", jwt_secret="x", service_area_version="test-gate",
                            allow_candidate_service_area=allow)
        with Session(db_engine) as session, pytest.raises(ApiError) as exc:
            active_service_areas(session, settings)
        assert exc.value.code == code
    finally:
        with db_engine.begin() as conn:
            conn.execute(text("DELETE FROM service_areas WHERE service_area_version = 'test-gate'"))


def test_existing_bundle_is_never_overwritten(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Evidence anti-overwrite: a second run must go to another --out directory."""
    sab.ensure_new_bundle(tmp_path / "sa-cand-new")          # absent: allowed
    (tmp_path / "sa-cand-new").mkdir()
    sab.ensure_new_bundle(tmp_path / "sa-cand-new")          # empty: allowed
    (tmp_path / "sa-cand-new" / "REVIEW.md").write_text("reviewed", encoding="utf-8")
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        sab.ensure_new_bundle(tmp_path / "sa-cand-new")


def test_excluded_layer_is_persisted_and_empty_mask_is_stable(db_engine: Engine, synthetic_units: None) -> None:
    """GEO-04: EXCLUDED is its own layer next to the raw TOTAL; an empty mask is valid and stable."""
    empty = "SELECT COALESCE(ST_Multi(ST_Union(geom)), ST_GeomFromText('MULTIPOLYGON EMPTY', 4326)) " \
            f"FROM {sab.SCHEMA}.units WHERE osm_id = ANY(:ids)"
    with db_engine.begin() as conn:
        assert sab.persist(conn, "test-v2", "TOTAL", sab.geometry_sql("units"), {"ids": [1, 2, 3]}, {}) == "inserted"
        assert sab.persist(conn, "test-v2", "EXCLUDED", empty, {"ids": [3]}, {}) == "inserted"
        assert sab.persist(conn, "test-v2", "EXCLUDED", empty, {"ids": [3]}, {}) == "unchanged (ST_Equals)"
        assert sab.persist(conn, "test-v3", "EXCLUDED", empty, {"ids": []}, {}) == "inserted"
        assert sab.persist(conn, "test-v3", "EXCLUDED", empty, {"ids": []}, {}) == "unchanged (ST_Equals)"
        raw = conn.execute(text("SELECT ST_Area(geom) FROM service_areas WHERE service_area_version = 'test-v2' "
                                "AND area_type = 'TOTAL'")).scalar_one()
        assert raw == pytest.approx(0.03)  # the raw TOTAL keeps the excluded unit


def test_tier1_sampled_point_rule_adds_partly_within_units() -> None:
    """GEO-03 / SF-P1-12: a unit whose representative point is beyond the limit but with
    a sampled point within it enters the polygon; its points beyond are left to tier 2."""
    b = _build({"rules_id": "r", "total": {"tier1_rule": "any_sample_within"}})
    info = {7: {"name": "U7", "province": "P", "road_km": 151.2, "snap_m": 12.0},
            8: {"name": "U8", "province": "P", "road_km": 149.0, "snap_m": 3.0}}
    total = [{"osm_id": 8, "name": "U8", "province": "P", "road_km": 149.0, "snap_m": 3.0, "rule": "T"}]
    sens = [{"osm_id": 7, "verdict": "EXCLUDED_PARTLY_WITHIN_LIMIT", "included": False},
            {"osm_id": 8, "verdict": "INCLUDED_PARTLY_BEYOND_LIMIT", "included": True}]
    added = sab.apply_tier1_samples(total, sens, info, b)
    assert [a["osm_id"] for a in added] == [7] and [t["osm_id"] for t in total] == [7, 8]
    assert sens[0]["verdict"] == "INCLUDED_PARTLY_BEYOND_LIMIT" and sens[0]["included"] is True
    legacy = [{"osm_id": 8}]
    v2_rules = _build({"rules_id": "r", "total": {"province_scope": "all_within_range"}})  # no tier1_rule
    assert sab.apply_tier1_samples(legacy, sens, info, v2_rules) == [] and legacy == [{"osm_id": 8}]
