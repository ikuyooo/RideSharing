"""Client half of staging_e2e.sh: one synthetic TEST response over HTTPS, TLS verified
against Caddy's internal root certificate (argv[1])."""

import sys

import httpx

BASE = "https://localhost:8443"


def main() -> None:
    root = sys.argv[1]
    with httpx.Client(base_url=BASE, verify=root, timeout=20, headers={"Connection": "close"}) as c:
        form = c.get("/survey/s1")
        assert form.status_code == 200 and "noindex" in form.text, form.status_code
        print(f"[stage] TLS verified against Caddy internal CA; GET /survey/s1 -> {form.status_code}; "
              f"HSTS={'strict-transport-security' in form.headers}; CSP={'content-security-policy' in form.headers}")
        for path in ("/api/admin/survey/s1/export/choices?dataset=TEST", "/docs", "/openapi.json", "/health/live",
                     "/api/trip-requests", "/api/auth/login"):
            r = c.get(path)
            assert r.status_code == 404, (path, r.status_code)
        print("[stage] admin / docs / health / trip / auth routes -> 404 through the proxy")
        s = c.post("/api/survey/s1/sessions", json={"group": "STUDENT"})
        assert s.status_code == 201, s.text
        body = s.json()
        assert body["dataset"] == "TEST", body["dataset"]
        d = body["design"]
        answer = {"start_token": body["start_token"],
                  "choices": [{"task_id": t["task_id"], "chosen": t["cards"][0]["alternative"]} for t in d["tasks"]],
                  "fairness": [{"display_label": f["display_label"], "likert": 3} for f in d["fairness"]],
                  "preferred_label": "X"}
        bad = c.post(f"/api/survey/s1/sessions/{body['respondent_id']}/submit", json=answer | {"email": "x@example.com"})
        assert bad.status_code == 422, bad.status_code
        ok = c.post(f"/api/survey/s1/sessions/{body['respondent_id']}/submit", json=answer)
        assert ok.status_code == 201, ok.text
        print(f"[stage] TEST session started + submitted over HTTPS (dataset {body['dataset']}); "
              f"unknown field rejected 422; flags {ok.json()['quality_flags']}")
        big = c.post("/api/survey/s1/sessions", content=b"x" * 70000, headers={"Content-Type": "application/json"})
        assert big.status_code in (400, 413), big.status_code
        print(f"[stage] 70 KB request body refused by the proxy -> {big.status_code}")


if __name__ == "__main__":
    main()
