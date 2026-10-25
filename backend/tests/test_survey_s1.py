"""Survey S1 DRAFT (owner decision P1-D5): design built only from the draft
questionnaire, anonymity, TEST/RESEARCH separation, export formats for
GroupKFold-by-respondent and the H4 tests. Data here is TEST data."""

import csv
import io
import itertools
import logging
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from tests.api_helpers import client, new_admin, new_user  # noqa: F401

pytestmark = pytest.mark.db


def _answer(design: dict, chosen_index: int = 0, likert: dict[str, int] | None = None) -> dict:
    return {
        "group": "STUDENT",
        "choices": [{"task_id": t["task_id"], "chosen": t["cards"][chosen_index]["alternative"]} for t in design["tasks"]],
        "fairness": [{"display_label": f["display_label"], "likert": (likert or {}).get(f["display_label"], 3)}
                     for f in design["fairness"]],
        "preferred_label": design["fairness"][0]["display_label"],
    }


def _start(client: TestClient) -> dict:
    resp = client.post("/api/survey/s1/sessions")
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
    assert prices == {"BIKE_URBAN": 81000, "CAR_URBAN_POOL": 143000, "CAR_URBAN_PRIVATE": 194000}
    assert all(next(c for c in t["cards"] if c["alternative"] == "CAR_INTERCITY_POOL")["fill_likelihood"] == "TBD"
               for t in t1b)
    q = load_questionnaire(Path(get_settings().survey_s1_questionnaire_path))
    rid = uuid.UUID(s["respondent_id"])
    assert build_design(q, rid, d["block"]) == d


def test_block_rotation_covers_all_pool_combinations() -> None:
    from pathlib import Path

    from app.modules.ml_models.survey_design import N_BLOCKS, build_design
    from app.modules.ml_models.survey_service import load_questionnaire
    from tests.conftest import QUESTIONNAIRE

    q = load_questionnaire(Path(QUESTIONNAIRE))
    seen = set()
    for block in range(N_BLOCKS):
        d = build_design(q, uuid.uuid4(), block)
        for t in d["tasks"]:
            for c in t["cards"]:
                if c["alternative"] == "CAR_URBAN_POOL":
                    seen.add((c["match_likelihood"], c["walk_m"]))
    assert seen == set(itertools.product(("HIGH", "MEDIUM", "LOW"), (0, 200)))


def test_submit_validation_and_single_submission(client: TestClient) -> None:
    s = _start(client)
    url = f"/api/survey/s1/sessions/{s['respondent_id']}/submit"
    full = _answer(s["design"])
    incomplete = full | {"choices": full["choices"][:-1]}
    assert client.post(url, json=incomplete).json()["error"]["code"] == "INCOMPLETE_CHOICES"
    wrong = full | {"choices": [dict(full["choices"][0], chosen="CAR_INTERCITY_PRIVATE")] + full["choices"][1:]}
    assert client.post(url, json=wrong).status_code == 422
    assert client.post(url, json=full | {"email": "someone@example.com"}).status_code == 422  # no PII fields
    assert client.post(url, json=full | {"demographics": {"ride_hailing_trips_per_week": "3-5"}}).status_code == 422
    ok = client.post(url, json=full)
    assert ok.status_code == 201, ok.text
    assert client.post(url, json=full).json()["error"]["code"] == "ALREADY_SUBMITTED"
    assert client.post(f"/api/survey/s1/sessions/{uuid.uuid4()}/submit", json=full).status_code == 404


def test_quality_flags(client: TestClient) -> None:
    s = _start(client)
    d = s["design"]
    same_position = {
        "group": "WORKER",
        "choices": [{"task_id": t["task_id"], "chosen": next(c["alternative"] for c in t["cards"] if c["position"] == 1)}
                    for t in d["tasks"]],
        "fairness": [{"display_label": f["display_label"], "likert": 4} for f in d["fairness"]],
        "preferred_label": "Y",
    }
    flags = client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit", json=same_position).json()["quality_flags"]
    assert flags == ["QC3_SAME_POSITION_ALL_1A", "QC4_SAME_LIKERT_ALL_METHODS"]


def test_research_dataset_blocked_until_release(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.settings import get_settings

    monkeypatch.setenv("SURVEY_DATASET", "RESEARCH")
    get_settings.cache_clear()
    resp = client.post("/api/survey/s1/sessions")
    assert resp.status_code == 403 and resp.json()["error"]["code"] == "SURVEY_NOT_RELEASED"


def test_storage_has_no_identity_link(db_session: Session) -> None:
    insp = inspect(db_session.get_bind())
    columns = {c["name"] for t in ("survey_respondents", "survey_responses") for c in insp.get_columns(t)}
    forbidden = {"user_id", "email", "name", "phone", "ip", "ip_address", "student_id", "gender"}
    assert not columns & forbidden
    fks = [fk["referred_table"] for t in ("survey_respondents", "survey_responses") for fk in insp.get_foreign_keys(t)]
    assert "users" not in fks


def test_export_formats_groupkfold_and_h4(client: TestClient, db_session: Session) -> None:
    for i in range(3):
        s = _start(client)
        assert client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit",
                           json=_answer(s["design"], chosen_index=i % 3, likert={"X": 5, "Y": 2, "Z": 4})).status_code == 201
    _start(client)  # an unfinished session is not exported
    _, admin = new_admin(client, db_session)
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
