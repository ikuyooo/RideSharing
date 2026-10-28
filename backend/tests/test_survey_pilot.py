"""OWNER APPROVAL s.4 item 7: internal TEST pilot of the Part-1A experiment with matrix D.

150 synthetic respondents (75 students / 75 workers) go through the real API and the
TEST dataset of the throwaway test database: session start (quota), design D switched
on IN MEMORY ONLY, choices simulated from the illustrative priors of survey_stats (an
assumption), submit, admin CSV export. The conditional logit is then estimated from
the EXPORTED rows, so the whole chain design -> API -> storage -> export -> estimation
is exercised. Research collection stays closed; pricing_configs is not touched.

Set S1_PILOT_EVIDENCE=<dir> to write the estimates as JSON evidence."""

import copy
import csv
import io
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.ml_models import survey_stats as st
from tests.api_helpers import client, new_admin  # noqa: F401
from tests.conftest import QUESTIONNAIRE

pytestmark = pytest.mark.db
N_PER_GROUP = 75
VARIANTS = {
    "D": {},  # owner-approved matrix D as in the questionnaire
    "D_bal": {"bike_time_mult": {"a": 1, "b": 1, "c": 1, "block_div": 2}},  # balance fix only
    "D2": "from questionnaire",  # proposed adjustment (variation_design_proposals.D2)
}


class AllowAll:
    def allow(self, bucket: str, client: str, limit: int, window_s: int) -> bool:
        return True


def encode_export(rows: list[dict[str, str]]) -> list[list[float]]:
    """Rebuild one choice set (ALTERNATIVES order) from exported long-format rows."""
    by = {r["alternative"]: r for r in rows}
    t = {"context": {"weather": rows[0]["weather"], "urgency": rows[0]["urgency"]}, "cards": []}
    for alt in st.ALTERNATIVES:
        r = by[alt]
        card = {"alternative": alt, "price_vnd": int(r["price_vnd"])}
        if r["travel_min"]:
            card["travel_min"] = int(r["travel_min"])
        if alt == "CAR_URBAN_POOL":
            card |= {"max_detour_min": int(r["max_detour_min"]), "match_likelihood": r["match_likelihood"],
                     "max_price_if_unmatched_vnd": int(r["max_price_if_unmatched_vnd"]), "walk_m": int(r["walk_m"])}
        t["cards"].append(card)
    return st.encode(t)


@pytest.mark.parametrize("variant", list(VARIANTS))
def test_pilot_matrix_d_is_estimable_from_exported_test_data(client: TestClient, db_session: Session,  # noqa: F811
                                                            monkeypatch: pytest.MonkeyPatch, variant: str) -> None:
    from app.modules.ml_models import survey_service
    from app.modules.ml_models.survey_api import get_rate_limiter

    real = survey_service.load_questionnaire
    base = copy.deepcopy(real(Path(QUESTIONNAIRE)))
    assert base["part_1a"]["variation_design"]["active"] is False  # the file itself stays off
    base["part_1a"]["variation_design"]["active"] = True
    changes = (base["part_1a"]["variation_design_proposals"]["D2"]["factor_overrides"] if variant == "D2"
               else VARIANTS[variant])
    factors = base["part_1a"]["variation_design"]["factors"]
    for name, change in changes.items():
        factors[name] = factors.get(name, {}) | change
    monkeypatch.setattr(survey_service, "load_questionnaire", lambda path: base)
    client.app.dependency_overrides[get_rate_limiter] = lambda: AllowAll()
    pricing_before = db_session.execute(text("SELECT count(*), md5(coalesce(string_agg(params_json::text, '' "
                                             "ORDER BY version, service_code), '')) FROM pricing_configs")).one()
    import random

    rng_seed = 20261028
    for n in range(2 * N_PER_GROUP):
        group = "STUDENT" if n % 2 == 0 else "WORKER"
        s = client.post("/api/survey/s1/sessions", json={"group": group}).json()
        choices = []
        for k, t in enumerate(s["design"]["tasks"]):
            if t["part"] == "1A":
                j = st.simulate([st.encode(t)], st.PRIORS, seed=rng_seed + 100 * n + k)[0]
                choices.append({"task_id": t["task_id"], "chosen": st.ALTERNATIVES[j]})
            else:
                choices.append({"task_id": t["task_id"], "chosen": random.Random(n + k).choice(t["cards"])["alternative"]})
        body = {"start_token": s["start_token"], "choices": choices, "preferred_label": "X",
                "fairness": [{"display_label": f["display_label"], "likert": 3} for f in s["design"]["fairness"]]}
        assert client.post(f"/api/survey/s1/sessions/{s['respondent_id']}/submit", json=body).status_code == 201
    _, admin = new_admin(client, db_session)
    resp = client.get("/api/admin/survey/s1/export/choices?dataset=TEST", headers=admin)
    assert resp.status_code == 200
    rows = [r for r in csv.DictReader(io.StringIO(resp.text)) if r["part"] == "1A"]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in rows:
        grouped.setdefault((r["respondent_id"], r["task_id"]), []).append(r)
    sets, chosen = [], []
    for task_rows in grouped.values():
        sets.append(encode_export(task_rows))
        chosen.append(st.ALTERNATIVES.index(next(r["alternative"] for r in task_rows if r["chosen"] == "1")))
    assert len(sets) == 2 * N_PER_GROUP * 8

    fit = st.fit_mnl(sets, chosen)
    assert fit["converged"]
    z = [(b - p) / se for b, p, se in zip(fit["beta"], st.PRIORS, fit["se"], strict=True)]
    t_price = fit["beta"][2] / fit["se"][2]
    t_time = fit["beta"][3] / fit["se"][3]
    result = {"variant": variant, "respondents": 2 * N_PER_GROUP, "choice_sets": len(sets),
              "log_likelihood": round(fit["log_likelihood"], 2),
              "parameters": {c: {"true_prior": p, "estimate": round(b, 4), "se": round(se, 4), "z_vs_true": round(zz, 2)}
                             for c, p, b, se, zz in zip(st.COLUMNS, st.PRIORS, fit["beta"], fit["se"], z, strict=True)},
              "t_price": round(t_price, 2), "t_time": round(t_time, 2)}
    if os.environ.get("S1_PILOT_EVIDENCE"):
        Path(os.environ["S1_PILOT_EVIDENCE"], f"s1_pilot_{variant}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(abs(x) < 3.5 for x in z), result          # true values recovered (no bias in the chain)
    assert t_price < -2, result                           # the price effect is estimable
    # The time effect's precision is a FINDING, reported in the evidence, not asserted:
    # with D it is not reliably estimable at N = 150 (design_diagnostics expected |t|).
    # research data untouched, pricing_configs unchanged, quota respected
    research = client.get("/api/admin/survey/s1/export/choices?dataset=RESEARCH", headers=admin)
    assert len(list(csv.DictReader(io.StringIO(research.text)))) == 0
    assert db_session.execute(text("SELECT count(*), md5(coalesce(string_agg(params_json::text, '' "
                                   "ORDER BY version, service_code), '')) FROM pricing_configs")).one() == pricing_before
    by_group = dict(db_session.execute(text("SELECT respondent_group, count(*) FROM survey_respondents "
                                            "WHERE completed_at IS NOT NULL GROUP BY 1")).all())
    assert by_group == {"STUDENT": N_PER_GROUP, "WORKER": N_PER_GROUP}
