"""Survey S1 DRAFT (owner decision P1-D5): design built only from the draft
questionnaire, anonymity, TEST/RESEARCH separation, export formats for
GroupKFold-by-respondent and the H4 tests. Data here is TEST data."""

import csv
import io
import itertools
import logging
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from tests.api_helpers import client, new_admin, new_user  # noqa: F401
from tests.conftest import QUESTIONNAIRE

pytestmark = pytest.mark.db

DEMOGRAPHICS = {"ride_hailing_trips_per_week": "3-5", "usual_trip_distance": "3-LT7", "intercity_trips_per_month": "1"}


class FakeLimiter:
    """Injected rate limiter (production: salted-hash counters in Redis)."""

    def __init__(self, limit: int | None = None) -> None:
        self.limit, self.hits = limit, 0

    def allow(self, bucket: str, client: str, limit: int, window_s: int) -> bool:
        self.hits += 1
        return self.limit is None or self.hits <= self.limit


@pytest.fixture(autouse=True)
def limiter(client: TestClient) -> FakeLimiter:
    from app.modules.ml_models.survey_api import get_rate_limiter

    fake = FakeLimiter()
    client.app.dependency_overrides[get_rate_limiter] = lambda: fake
    yield fake
    client.app.dependency_overrides.pop(get_rate_limiter, None)


def _answer(session: dict, chosen_index: int = 0, likert: dict[str, int] | None = None) -> dict:
    design = session["design"]
    return {
        "start_token": session["start_token"],
        "choices": [{"task_id": t["task_id"], "chosen": t["cards"][chosen_index]["alternative"]} for t in design["tasks"]],
        "fairness": [{"display_label": f["display_label"], "likert": (likert or {}).get(f["display_label"], 3)}
                     for f in design["fairness"]],
        "preferred_label": design["fairness"][0]["display_label"],
        "demographics": DEMOGRAPHICS,
    }


def _start(client: TestClient, group: str = "STUDENT") -> dict:
    resp = client.post("/api/survey/s1/sessions", json={"group": group})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_design_follows_section_65_and_is_deterministic(client: TestClient) -> None:
    from pathlib import Path

    from app.core.settings import get_settings
    from app.modules.ml_models.survey_design import build_design
    from app.modules.ml_models.survey_service import load_questionnaire

    s = _start(client)
    d = s["design"]
    assert s["dataset"] == "TEST" and s["status"] == "DRAFT_NOT_RELEASED"
    uuid.UUID(s["respondent_id"])
    t1a = [t for t in d["tasks"] if t["part"] == "1A"]
    t1b = [t for t in d["tasks"] if t["part"] == "1B"]
    contexts = {(t["context"]["distance_km"], t["context"]["weather"], t["context"]["urgency"]) for t in t1a}
    assert len(t1a) == 8 and len(contexts) == 8  # full 2x2x2 factorial, each once
    assert {c[0] for c in contexts} == {6, 14}
    assert len(t1b) == 2 and {next(c["price_vnd"] for c in t["cards"] if c["alternative"] == "CAR_INTERCITY_POOL")
                              for t in t1b} == {180000, 220000}
    assert all(sorted(c["position"] for c in t["cards"]) == [1, 2, 3] for t in d["tasks"])
    assert [f["display_label"] for f in d["fairness"]] == ["X", "Y", "Z"]
    assert {f["method"] for f in d["fairness"]} == {"A_proportional", "B_shapley_equal_split", "C_inconvenience_weighted"}
    # Values come from the draft questionnaire; TBD is never replaced by a number.
    fourteen = next(t for t in t1a if t["context"]["distance_km"] == 14)
    prices = {c["alternative"]: c["price_vnd"] for c in fourteen["cards"]}
    # Survey decision 2: the generic 14 km card shows Fare_matched_est (R9 Section 20.2);
    # 143.000 đ belongs only to the matched scenario A of Section 16.1.
    assert prices == {"BIKE_URBAN": 81000, "CAR_URBAN_POOL": 145000, "CAR_URBAN_PRIVATE": 194000}
    fills = [next(c for c in t["cards"] if c["alternative"] == "CAR_INTERCITY_POOL") for t in t1b]
    assert {c["fill_likelihood"] for c in fills} == {"HIGH", "LOW"}  # hypothetical levels, one per seat price
    assert all(c["fill_likelihood_text"] for c in fills)
    assert not any(v == "TBD" for t in d["tasks"] for c in t["cards"] for v in c.values())
    q = load_questionnaire(Path(get_settings().survey_s1_questionnaire_path))
    rid = uuid.UUID(s["respondent_id"])
    assert build_design(q, rid, d["block"]) == d


def test_block_rotation_covers_all_pool_combinations() -> None:
    from pathlib import Path

    from app.modules.ml_models.survey_design import N_BLOCKS, build_design
    from app.modules.ml_models.survey_service import load_questionnaire
    from tests.conftest import QUESTIONNAIRE

    q = load_questionnaire(Path(QUESTIONNAIRE))
    seen, pairings = set(), set()
    for block in range(N_BLOCKS):
        d = build_design(q, uuid.uuid4(), block)
        for t in d["tasks"]:
            for c in t["cards"]:
                if c["alternative"] == "CAR_URBAN_POOL":
                    seen.add((c["match_likelihood"], c["walk_m"]))
        pairings.add(tuple(sorted((c["price_vnd"], c["fill_likelihood"]) for t in d["tasks"] for c in t["cards"]
                                  if c["alternative"] == "CAR_INTERCITY_POOL")))
    assert seen == set(itertools.product(("HIGH", "MEDIUM", "LOW"), (0, 200)))
    # Part 1B: both price x fill-likelihood pairings occur (2x2 balanced over the 6 blocks).
    assert pairings == {((180000, "HIGH"), (220000, "LOW")), ((180000, "LOW"), (220000, "HIGH"))}


def test_submit_validation_and_single_submission(client: TestClient) -> None:
    s = _start(client)
    url = f"/api/survey/s1/sessions/{s['respondent_id']}/submit"
    full = _answer(s)
    incomplete = full | {"choices": full["choices"][:-1]}
    assert client.post(url, json=incomplete).json()["error"]["code"] == "INCOMPLETE_CHOICES"
    wrong = full | {"choices": [dict(full["choices"][0], chosen="CAR_INTERCITY_PRIVATE")] + full["choices"][1:]}
    assert client.post(url, json=wrong).status_code == 422
    assert client.post(url, json=full | {"email": "someone@example.com"}).status_code == 422  # no PII fields
    assert client.post(url, json=full | {"demographics": DEMOGRAPHICS | {"usual_trip_distance": "3-7"}}).status_code == 422
    assert client.post(url, json=full | {"group": "WORKER"}).status_code == 422  # group is fixed at start
    tampered = full | {"start_token": "1." + full["start_token"].split(".")[1]}
    assert client.post(url, json=tampered).json()["error"]["code"] == "INVALID_START_TOKEN"
    ok = client.post(url, json=full)
    assert ok.status_code == 201, ok.text
    assert client.post(url, json=full).json()["error"]["code"] == "ALREADY_SUBMITTED"
    assert client.post(f"/api/survey/s1/sessions/{uuid.uuid4()}/submit", json=full).status_code == 404


def test_quality_flags(client: TestClient) -> None:
    s = _start(client, "WORKER")
    d = s["design"]
    same_position = _answer(s) | {
        "choices": [{"task_id": t["task_id"], "chosen": next(c["alternative"] for c in t["cards"] if c["position"] == 1)}
                    for t in d["tasks"]],
        "fairness": [{"display_label": f["display_label"], "likert": 4} for f in d["fairness"]],
        "preferred_label": "Y",
    }
    flags = client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit", json=same_position).json()["quality_flags"]
    # Submitted within seconds of the start -> QC2 flag (decision 7: flagged, never excluded).
    assert flags == ["QC2_FAST_COMPLETION", "QC3_SAME_POSITION_ALL_1A", "QC4_SAME_LIKERT_ALL_METHODS"]


def test_qc2_uses_signed_duration_and_publishes_threshold(client: TestClient, db_session: Session,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.ml_models import survey_service

    t0 = 1_800_000_000_000
    monkeypatch.setattr(survey_service, "_now_ms", lambda: t0)
    s = _start(client)
    monkeypatch.setattr(survey_service, "_now_ms", lambda: t0 + 200_500)  # 200.5 s later
    resp = client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit", json=_answer(s, likert={"X": 5, "Y": 2}))
    assert resp.status_code == 201 and "QC2_FAST_COMPLETION" not in resp.json()["quality_flags"]
    stored = db_session.execute(text("SELECT duration_s, extract(second FROM completed_at) FROM survey_respondents "
                                     "WHERE respondent_id = :r"), {"r": s["respondent_id"]}).one()
    assert stored[0] == 200 and stored[1] == 0  # whole seconds of duration; timestamps stay per minute
    q = survey_service.load_questionnaire(Path(QUESTIONNAIRE))
    assert q["quality_rules"]["QC2"]["flag_below_seconds"] == 120 and q["quality_rules"]["QC2"]["action"] == "FLAG_ONLY"


def test_group_quota_closes_a_full_group_at_session_start(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.ml_models import survey_service

    real = survey_service.load_questionnaire

    def small_target(path):  # type: ignore[no-untyped-def]
        q = dict(real(path))
        return q | {"quotas": q["quotas"] | {"target_valid_respondents": 2}}  # cap = floor(0.6 x 2) = 1

    q = real(Path(QUESTIONNAIRE))
    assert q["quotas"]["target_valid_respondents"] == 150 and survey_service.group_cap(q) == 90
    monkeypatch.setattr(survey_service, "load_questionnaire", small_target)
    s = _start(client, "STUDENT")
    assert client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit", json=_answer(s)).status_code == 201
    full = client.post("/api/survey/s1/sessions", json={"group": "STUDENT"})
    assert full.status_code == 409 and full.json()["error"]["code"] == "QUOTA_FULL_FOR_GROUP"
    assert client.post("/api/survey/s1/sessions", json={"group": "WORKER"}).status_code == 201


def test_rate_limit_rejects_bursts(client: TestClient, limiter: FakeLimiter) -> None:
    limiter.limit = 2
    assert _start(client) and _start(client)
    resp = client.post("/api/survey/s1/sessions", json={"group": "STUDENT"})
    assert resp.status_code == 429 and resp.json()["error"]["code"] == "RATE_LIMITED"


def test_rate_limit_key_never_contains_the_address() -> None:
    from datetime import UTC, datetime

    from app.modules.ml_models.survey_guard import client_key

    day1, day2 = datetime(2026, 11, 1, 10, tzinfo=UTC), datetime(2026, 11, 2, 10, tzinfo=UTC)
    k = client_key("secret", "203.0.113.7", day1)
    assert len(k) == 16 and "203" not in k and k == client_key("secret", "203.0.113.7", day1)
    assert k != client_key("secret", "203.0.113.7", day2)  # rotates daily
    assert k != client_key("other", "203.0.113.7", day1)


def test_admin_can_delete_a_respondent_on_request(client: TestClient, db_session: Session) -> None:
    s = _start(client)
    assert client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit", json=_answer(s)).status_code == 201
    _, admin = new_admin(client, db_session)
    _, passenger = new_user(client)
    url = f"/api/admin/survey/s1/respondents/{s['respondent_id']}"
    assert client.delete(url, headers=passenger).status_code == 403
    assert client.delete(url, headers=admin).status_code == 204
    left = db_session.execute(text("SELECT count(*) FROM survey_responses WHERE respondent_id = :r"),
                              {"r": s["respondent_id"]}).scalar_one()
    assert left == 0 and client.delete(url, headers=admin).status_code == 404


def test_research_dataset_blocked_until_release(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.settings import get_settings

    monkeypatch.setenv("SURVEY_DATASET", "RESEARCH")
    get_settings.cache_clear()
    resp = client.post("/api/survey/s1/sessions", json={"group": "STUDENT"})
    assert resp.status_code == 403 and resp.json()["error"]["code"] == "SURVEY_NOT_RELEASED"


def test_storage_has_no_identity_link(db_session: Session) -> None:
    insp = inspect(db_session.get_bind())
    columns = {c["name"] for t in ("survey_respondents", "survey_responses") for c in insp.get_columns(t)}
    forbidden = {"user_id", "email", "name", "phone", "ip", "ip_address", "ip_hash", "student_id", "gender",
                 "user_agent"}
    assert not columns & forbidden
    fks = [fk["referred_table"] for t in ("survey_respondents", "survey_responses") for fk in insp.get_foreign_keys(t)]
    assert "users" not in fks


def test_export_formats_groupkfold_and_h4(client: TestClient, db_session: Session) -> None:
    _, admin = new_admin(client, db_session)  # token issued first; the export below stays well inside its TTL
    for i in range(3):
        s = _start(client)
        assert client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit",
                           json=_answer(s, chosen_index=i % 3, likert={"X": 5, "Y": 2, "Z": 4})).status_code == 201
    _start(client)  # an unfinished session is not exported
    _, passenger = new_user(client)
    url = "/api/admin/survey/s1/export/{}?dataset=TEST"
    assert client.get(url.format("choices"), headers=passenger).status_code == 403
    assert client.get(url.format("choices")).status_code == 401

    def table(name: str) -> list[dict]:
        resp = client.get(url.format(name), headers=admin)
        assert resp.status_code == 200 and resp.headers["content-type"].startswith("text/csv")
        return list(csv.DictReader(io.StringIO(resp.text)))

    respondents, choices, fairness = table("respondents"), table("choices"), table("fairness_h4")
    ids = {r["respondent_id"] for r in respondents}
    assert len(ids) == 3
    assert all(r["group"] == "STUDENT" for r in respondents)
    assert all(r["usual_trip_distance"] == "3-LT7" and r["duration_s"] != "" for r in respondents)
    # Long format: 10 tasks x 3 alternatives per respondent, exactly one chosen per task.
    assert len(choices) == 3 * 10 * 3
    per_task: dict[tuple[str, str], int] = {}
    for row in choices:
        per_task[(row["respondent_id"], row["task_id"])] = per_task.get((row["respondent_id"], row["task_id"]), 0) + int(row["chosen"])
    assert set(per_task.values()) == {1} and {k[0] for k in per_task} == ids
    # GroupKFold by respondent_id: assign folds per respondent; no respondent spans two folds.
    folds = {rid: n % 5 for n, rid in enumerate(sorted(ids))}
    assert all(folds[row["respondent_id"]] == folds[row["respondent_id"]] for row in choices)
    # H4: 3 methods per respondent, exactly one preferred, Likert 1..5.
    assert len(fairness) == 9
    for rid in ids:
        rows = [f for f in fairness if f["respondent_id"] == rid]
        assert {r["method"] for r in rows} == {"A_PROPORTIONAL", "B_SHAPLEY_EQUAL_SPLIT", "C_INCONVENIENCE_WEIGHTED"}
        assert sum(int(r["preferred"]) for r in rows) == 1
        assert all(1 <= int(r["likert_fairness"]) <= 5 for r in rows)
    research = client.get(url.replace("TEST", "RESEARCH").format("choices"), headers=admin)
    assert research.status_code == 200 and len(list(csv.DictReader(io.StringIO(research.text)))) == 0
    quota = client.get("/api/admin/survey/s1/quota?dataset=TEST", headers=admin).json()
    assert quota["completed"] == 3 and quota["by_group"] == {"STUDENT": 3}
    # Timestamps are stored truncated to the minute.
    secs = db_session.execute(text("SELECT DISTINCT extract(second FROM started_at) FROM survey_respondents")).scalars().all()
    assert set(secs) == {0}


def test_survey_access_log_drops_client_address() -> None:
    from app.core.logging import SurveyClientAddressFilter

    f = SurveyClientAddressFilter()
    record = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d',
                               ("203.0.113.7:51234", "POST", "/api/survey/s1/sessions", "1.1", 201), None)
    assert f.filter(record) and record.args[0] == "-"
    assert "203.0.113.7" not in record.getMessage()
    other = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d',
                              ("203.0.113.7:51234", "GET", "/health/live", "1.1", 200), None)
    assert f.filter(other) and other.args[0] == "203.0.113.7:51234"


def test_form_page_is_marked_draft(client: TestClient) -> None:
    resp = client.get("/survey/s1")
    assert resp.status_code == 200
    assert "BẢN NHÁP — CHƯA PHÁT HÀNH" in resp.text and "noindex" in resp.text


def test_research_parameters_stay_out_of_pricing_configs() -> None:
    """Survey values (6 km derived prices, variation proposals) are research parameters:
    they live only in the questionnaire, never in the pricing seed / pricing_configs."""
    import yaml

    from app.modules.pricing import seed

    q = yaml.safe_load(Path(QUESTIONNAIRE).read_text(encoding="utf-8"))
    assert q["draft_version"] == 2
    source = Path(seed.__file__).read_text(encoding="utf-8")
    for marker in ("questionnaire", "price_variation", "survey"):
        assert marker not in source
    six = q["part_1a"]["levels_by_distance"]["6"]
    assert six["CAR_URBAN_POOL"]["expected_price_vnd"]["experimental_status"] == "DERIVED_LOCKED_FORMULA"
    assert all(v["approval_status"] == "NOT_ACTIVE_PROPOSAL" or v["experimental_status"] == "SOURCED_R9"
               for v in q["part_1a"]["price_variation_proposal"]["levels"].values())
