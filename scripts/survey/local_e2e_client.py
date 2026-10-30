"""Client half of local_e2e.sh: the whole survey S1 pipeline on the local stack with
SYNTHETIC respondents (owner "DEVELOPMENT FIRST": synthetic data may test the pipeline,
never stand in for survey results).

form -> session start (quota, design D2) -> submit (choices simulated from the
illustrative priors of survey_stats, an ASSUMPTION) -> abandoned sessions (rule R1) ->
rejected submissions (rule R3) -> admin quota / rejection counters / CSV export ->
conditional logit estimated from the EXPORTED rows (full and lean primary spec).

Usage: python -I local_e2e_client.py <base_url> <admin_email> <admin_password> <evidence.json>
"""

import csv
import io
import json
import random
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.modules.ml_models import survey_stats as st  # noqa: E402

N_PER_GROUP = 75
ABANDONED = 16
SEED = 20261029
LEAN = ["asc_bike", "asc_pool", "price_k", "time_min", "like_medium", "like_low", "walk_200", "rain_x_bike"]


def encode_export(rows: list[dict[str, str]]) -> list[list[float]]:
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


def main() -> None:
    base, email, password, out = sys.argv[1:5]
    with httpx.Client(base_url=base, timeout=30, headers={"Connection": "close"}) as c:
        form = c.get("/survey/s1")
        assert form.status_code == 200 and "s1_completed" in form.text, form.status_code
        submitted = 0
        for n in range(2 * N_PER_GROUP + ABANDONED):
            group = "STUDENT" if n % 2 == 0 else "WORKER"
            s = c.post("/api/survey/s1/sessions", json={"group": group})
            assert s.status_code == 201, s.text
            body = s.json()
            assert body["dataset"] == "TEST" and body["design"]["block"] in range(6)
            if n >= 2 * N_PER_GROUP:
                continue  # abandoned: never submitted (rule R1)
            choices = []
            for k, t in enumerate(body["design"]["tasks"]):
                if t["part"] == "1A":
                    j = st.simulate([st.encode(t)], st.PRIORS, seed=SEED + 100 * n + k)[0]
                    choices.append({"task_id": t["task_id"], "chosen": st.ALTERNATIVES[j]})
                else:
                    choices.append({"task_id": t["task_id"],
                                    "chosen": random.Random(SEED + n + k).choice(t["cards"])["alternative"]})
            answer = {"start_token": body["start_token"], "choices": choices, "preferred_label": "X",
                      "fairness": [{"display_label": f["display_label"], "likert": 3} for f in body["design"]["fairness"]]}
            url = f"/api/survey/s1/sessions/{body['respondent_id']}/submit"
            if n < 2:  # rule R3: one schema rejection and one forged token, then the real answer
                assert c.post(url, json=answer | {"email": "x@example.com"}).status_code == 422
                assert c.post(url, json=answer | {"start_token": "1.forged"}).status_code == 422
            r = c.post(url, json=answer)
            assert r.status_code == 201, r.text
            submitted += 1
        print(f"[local] {submitted} synthetic TEST respondents submitted, {ABANDONED} sessions abandoned")

        token = c.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
        admin = {"Authorization": f"Bearer {token}"}
        quota = c.get("/api/admin/survey/s1/quota?dataset=TEST", headers=admin).json()
        assert quota["completed"] == 2 * N_PER_GROUP and quota["started"] == 2 * N_PER_GROUP + ABANDONED, quota
        rej = c.get("/api/admin/survey/s1/rejections?days=2", headers=admin).json()
        assert rej["total_by_code"] == {"INVALID_START_TOKEN": 2, "REQUEST_VALIDATION": 2}, rej
        print(f"[local] quota: started {quota['started_by_group']}, completed {quota['by_group']}, "
              f"completion rate {quota['completion_rate_by_group']}; rejections {rej['total_by_code']}")

        tables = {}
        for name in ("respondents", "choices", "fairness_h4"):
            resp = c.get(f"/api/admin/survey/s1/export/{name}?dataset=TEST", headers=admin)
            assert resp.status_code == 200, resp.status_code
            tables[name] = list(csv.DictReader(io.StringIO(resp.text)))
        research = c.get("/api/admin/survey/s1/export/choices?dataset=RESEARCH", headers=admin)
        assert research.status_code == 200 and not list(csv.DictReader(io.StringIO(research.text)))
        assert len(tables["respondents"]) == 2 * N_PER_GROUP and len(tables["fairness_h4"]) == 3 * 2 * N_PER_GROUP

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in tables["choices"]:
        if r["part"] == "1A":
            grouped.setdefault((r["respondent_id"], r["task_id"]), []).append(r)
    sets, chosen = [], []
    for rows in grouped.values():
        sets.append(encode_export(rows))
        chosen.append(st.ALTERNATIVES.index(next(r["alternative"] for r in rows if r["chosen"] == "1")))
    assert len(sets) == 2 * N_PER_GROUP * 8

    full = st.fit_mnl(sets, chosen)
    keep = [st.COLUMNS.index(x) for x in LEAN]
    lean = st.fit_mnl([[[row[i] for i in keep] for row in xs] for xs in sets], chosen)
    assert full["converged"] and lean["converged"]
    z = [(b - p) / se for b, p, se in zip(full["beta"], st.PRIORS, full["se"], strict=True)]
    assert all(abs(x) < 3.5 for x in z), z
    assert full["beta"][2] / full["se"][2] < -2

    def table(fit: dict, cols: list[str]) -> dict:
        return {col: {"estimate": round(b, 4), "se": round(se, 4), "t": round(b / se, 2)}
                for col, b, se in zip(cols, fit["beta"], fit["se"], strict=True)}

    evidence = {
        "label": "SYNTHETIC TEST DATA - pipeline check only, NOT survey results",
        "design": "D2 (active local TEST design)", "dataset": "TEST",
        "respondents_submitted": submitted, "sessions_abandoned": ABANDONED, "choice_sets": len(sets),
        "simulation_priors_assumption": dict(zip(st.COLUMNS, st.PRIORS, strict=True)),
        "quota": {k: quota[k] for k in ("started_by_group", "by_group", "completion_rate_by_group")},
        "rejections_total_by_code": rej["total_by_code"],
        "full_spec": table(full, st.COLUMNS) | {"z_vs_simulation_prior_max_abs": round(max(abs(x) for x in z), 2)},
        "lean_primary_spec": table(lean, LEAN),
        "note": "the lean model omits terms present in the simulation, so its estimates are not compared with the priors",
    }
    Path(out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"[local] MNL from export: full spec max |z| vs priors {evidence['full_spec']['z_vs_simulation_prior_max_abs']}, "
          f"t(price) {evidence['full_spec']['price_k']['t']}, t(time) full {evidence['full_spec']['time_min']['t']} / "
          f"lean {evidence['lean_primary_spec']['time_min']['t']}")


if __name__ == "__main__":
    main()
