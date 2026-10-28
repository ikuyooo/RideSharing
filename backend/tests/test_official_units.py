"""GEO-06 / GEO-02: the transcribed official table (QĐ 19/2025/QĐ-TTg codes, NQ
1656/NQ-UBTVQH15 clauses) and the controlled urban list of the v3 rules. Pure
file checks; geometry is evaluated by the build pipeline."""

import csv
from pathlib import Path

import yaml

from app.modules.trip.service_area_build import norm_name

CONFIG = Path(__file__).resolve().parents[2] / "config"
OFFICIAL = CONFIG / "official" / "hanoi_units_qd19_nq1656.csv"
RULES_V3 = CONFIG / "service_area_rules.candidate.v3.yaml"


def _official() -> list[dict[str, str]]:
    with OFFICIAL.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_official_table_matches_qd19_totals() -> None:
    rows = _official()
    assert len(rows) == 126 and len({r["qd19_code"] for r in rows}) == 126
    assert sum(r["type"] == "PHUONG" for r in rows) == 51 and sum(r["type"] == "XA" for r in rows) == 75
    wards = {r["nq1656_clause"]: r["name"] for r in rows if r["type"] == "PHUONG"}
    assert set(wards) == {f"k{i}" for i in range(1, 52)}  # NQ1656 Điều 1 k1-k51 are the wards
    assert all(r["verification"].startswith("OFFICIALLY_VERIFIED") for r in rows)


def test_controlled_urban_list_is_traced_and_excludes_reviewed_units() -> None:
    rules = yaml.safe_load(RULES_V3.read_text(encoding="utf-8"))
    official = {r["qd19_code"]: r for r in _official()}
    units = rules["urban"]["include_units"]
    for u in units:
        ref = official[u["qd19_code"]]
        assert norm_name(ref["name"]) == norm_name(u["name"]) and ref["nq1656_clause"] == u["nq1656"], u
    names = {u["name"] for u in units}
    assert len(units) == 49 and "Xã Gia Lâm" in names
    for excluded in ("Phường Tùng Thiện", "Phường Sơn Tây", "Phường Chương Mỹ", "Xã Đông Anh", "Xã Thư Lâm",
                     "Xã Phúc Thịnh", "Xã An Khánh", "Xã Sơn Đồng"):
        assert excluded not in names
    assert "include_city_wards" not in rules["urban"]  # no "every ward is urban" rule (GEO-02)
    assert rules["serviceability"]["max_snap_m"] > 0 and rules["total"]["tier1_rule"] == "any_sample_within"


def test_name_normalisation_only_unifies_tone_mark_placement() -> None:
    assert norm_name("Phường Yên Hoà") == norm_name("Phường Yên Hòa")
    assert norm_name("Xã Thuỵ Lâm") == norm_name("Xã Thụy Lâm")
    assert norm_name("Phường Tây Hồ") != norm_name("Phường Tây Mỗ")


def test_rules_v4_hardening() -> None:
    """GEO-B/C/D/E: v4 keeps the v3 controlled urban list and adds the provable tier-1
    envelope, the ferry exclusion and the owner-approved 300 m snap threshold."""
    v3 = yaml.safe_load(RULES_V3.read_text(encoding="utf-8"))
    v4 = yaml.safe_load((CONFIG / "service_area_rules.candidate.v4.yaml").read_text(encoding="utf-8"))
    assert v4["urban"]["include_units"] == v3["urban"]["include_units"]
    assert v4["urban"]["include_osm_areas"] == v3["urban"]["include_osm_areas"]
    assert v4["total"]["tier1_rule"] == "geodesic_lower_bound"
    assert v4["serviceability"] == {"max_snap_m": 300, "exclude": ["ferry"]}
    review = {x["name"]: x["status"] for x in v4["urban"]["excluded_review"]}
    assert review["Phường Sơn Tây"].endswith("GEO-B (MVP)") and review["Phường Chương Mỹ"].endswith("GEO-B (MVP)")
    assert "PENDING_GEOMETRY_EVIDENCE" in review["Xã Đông Anh"]


def test_rules_v5_adds_only_the_former_dong_anh_town() -> None:
    """v5 = v4 + the pre-2025 town polygon (U4); no whole commune, no Global Gate, same envelope."""
    v4 = yaml.safe_load((CONFIG / "service_area_rules.candidate.v4.yaml").read_text(encoding="utf-8"))
    v5 = yaml.safe_load((CONFIG / "service_area_rules.candidate.v5.yaml").read_text(encoding="utf-8"))
    assert v5["urban"]["include_units"] == v4["urban"]["include_units"]
    assert v5["urban"]["include_osm_areas"] == v4["urban"]["include_osm_areas"]
    assert [h["relation"] for h in v5["urban"]["include_historic_areas"]] == [17627914]
    assert v5["urban"]["include_historic_areas"][0]["status"] == "PENDING_OWNER_APPROVAL"
    assert v5["total"] == v4["total"] and v5["serviceability"] == v4["serviceability"]
    names = {u["name"] for u in v5["urban"]["include_units"]}
    assert not names & {"Xã Đông Anh", "Xã Thư Lâm", "Xã Phúc Thịnh"}
