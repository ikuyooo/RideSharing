"""P2.4 - candidate generation benchmark and independent "0 violations" check
(Revision 9 Section 79 P2: "0 vi phạm ràng buộc cứng; độ trễ sinh ứng viên < 300 ms";
Section 77: "Lọc không gian PostGIS + Gọi 1 ma trận OSRM Table : p95 <= 300 ms").

SYNTHETIC fleets and trips (seeded) on a THROWAWAY database `p2_bench`, real OSRM
services of the compose stack. Per configuration (drivers x open pool plans) it times
every stage of `candidate.generator.generate` and re-verifies EVERY candidate with an
independent checker: OSRM /route legs along the candidate's stop chain (not the table
used by the generator), windows / limits / fares recomputed from the database rows.
Nothing is tuned to the target: N_single = 15, N_pool = 20, k_max = 8, R_urban = 5 km.

Latency must be measured INSIDE the compose network (backend -> osrm-*:5000, postgres:5432),
where the backend runs: from the Windows host, Docker Desktop's port proxy adds ~1 s per new
connection (measured 2026-10-29), which says nothing about the system.

Usage (repo root, stack running):
    MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v "$(pwd -W):/repo" backend         python -I /repo/scripts/p2_benchmark.py --in-network [--requests 200] [--seed 20261029]
"""

import argparse
import json
import math
import os
import platform
import random
import statistics
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import app  # noqa: E402,F401  bind `app` to this checkout before alembic prepends its own cwd

import httpx  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, make_url, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

sys.path.insert(0, str(ROOT / "backend" / "tests"))
import p2_fixtures as fx  # noqa: E402

DB = "p2_bench"
CENTER = (105.8520, 21.0285)
CONFIGS = [(50, 0), (200, 0), (1000, 0), (200, 10), (200, 20), (1000, 20)]
TOL_S, TOL_M = 1.0, 1.0  # per leg: OSRM /route vs /table rounding


def dotenv() -> dict[str, str]:
    path, env = ROOT / ".env", {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def admin_engine(base_url: str):  # noqa: ANN201
    return create_engine(make_url(base_url).set(database="postgres"), isolation_level="AUTOCOMMIT")


def recreate(base_url: str) -> str:
    with admin_engine(base_url).connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{DB}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{DB}"'))
    return make_url(base_url).set(database=DB).render_as_string(hide_password=False)


def drop(base_url: str) -> None:
    with admin_engine(base_url).connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{DB}" WITH (FORCE)'))


def migrate(url: str) -> None:
    cfg = Config(str(ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "backend" / "alembic"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")


def disk(rng: random.Random, center: tuple[float, float], r_km: float) -> tuple[float, float]:
    r, a = r_km * math.sqrt(rng.random()), rng.uniform(0, 2 * math.pi)
    return (center[0] + r * math.cos(a) / (111.32 * math.cos(math.radians(center[1]))), center[1] + r * math.sin(a) / 110.57)


def pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    return round(s[min(len(s) - 1, max(0, math.ceil(p / 100 * len(s)) - 1))], 2)


def summary(values: list[float]) -> dict:
    return {"n": len(values), "p50": pct(values, 50), "p95": pct(values, 95), "p99": pct(values, 99),
            "max": round(max(values), 2) if values else None, "mean": round(statistics.fmean(values), 2) if values else None}


class OsrmLegs:
    """Independent OSRM access for the verifier: /route legs, raw httpx."""

    def __init__(self, urls: dict[str, str]) -> None:
        self.urls = urls
        self._memo: dict[tuple, list[tuple[float, float]] | None] = {}

    def legs(self, profile: str, pts: list[tuple[float, float]]) -> list[tuple[float, float]] | None:
        key = (profile, tuple(pts))
        if key not in self._memo:
            self._memo[key] = self._legs(profile, pts)
        return self._memo[key]

    def _legs(self, profile: str, pts: list[tuple[float, float]]) -> list[tuple[float, float]] | None:
        path = ";".join(f"{x:.6f},{y:.6f}" for x, y in pts)
        body = httpx.get(f"{self.urls[profile]}/route/v1/driving/{path}",
                         # Each leg independent, as the /table pairs that R9 Sections 34 / 36 specify
                         # (car default continue_straight=true forbids U-turns at waypoints; SF-P2-15).
                         params={"overview": "false", "steps": "false", "exclude": "ferry", "continue_straight": "false"},
                         headers={"Connection": "close"}, timeout=10).json()
        if body.get("code") != "Ok":
            return None
        return [(leg["distance"], leg["duration"]) for leg in body["routes"][0]["legs"]]


def window(trip: dict, service: str) -> tuple[datetime, datetime]:
    lo_min, hi_min = (3, 15) if service == "BIKE_URBAN" else (5, 20)   # R9 Section 2.2 / Baseline
    pref = trip["preferred_departure"]
    return pref + timedelta(minutes=lo_min), pref + timedelta(minutes=hi_min)  # NOW trips, no own window


def fare(base: int, per_km: int, per_min: int, m: float, s: float) -> int:
    return int((base + per_km * m / 1000 + per_min * s / 60) // 1000) * 1000


def verify(c, session, osrm: OsrmLegs, trip: dict, now: datetime) -> tuple[set[str], set[str]]:  # noqa: ANN001
    """Independent re-derivation of the 11 constraints of R9 Section 7 for one candidate."""
    bad, edge = set(), set()
    profile = "motorbike" if c.service_code == "BIKE_URBAN" else "car"
    d = session.execute(text(
        "SELECT dl.availability, ST_X(dl.geom) x, ST_Y(dl.geom) y, EXTRACT(EPOCH FROM (:now - dl.updated_at)) age, "
        "dp.kyc_status, dp.accepts_urban, dp.pool_enabled, dp.max_additional_pickups, dp.max_driver_detour_km, "
        "dp.max_driver_detour_min, v.vehicle_type, v.capacity, v.is_active FROM driver_locations dl "
        "JOIN driver_profiles dp ON dp.user_id = dl.driver_id JOIN vehicles v ON v.id = dl.active_vehicle_id "
        "WHERE dl.driver_id = :d"), {"d": c.driver_id, "now": now}).mappings().one()
    new_vehicle = c.source_type == "NEW_SINGLE_VEHICLE"
    if (d["availability"] == "OFFLINE" or d["age"] > 120 or (new_vehicle and d["availability"] != "IDLE")
            or not d["is_active"] or d["vehicle_type"] != ("BIKE" if c.service_code == "BIKE_URBAN" else "CAR4")
            or not d["accepts_urban"]
            or (c.service_code == "CAR_URBAN_POOL" and (not d["pool_enabled"] or d["kyc_status"] != "VERIFIED"))):
        bad.add("HC01")
    if c.service_code not in trip["allowed_service_codes"]:
        bad.add("HC09")
    # riders and stop coordinates
    riders = {"new": {"seats": trip["passenger_count"], "onboard": False, "window": window(trip, c.service_code),
                      "pick": trip["p"], "drop": trip["q"], "same_gender": False}}
    direct = osrm.legs(profile, [trip["p"], trip["q"]])
    if direct is None:
        return {"HC02"}, edge
    riders["new"] |= {"direct": direct[0], "traveled": 0.0}
    if c.service_code == "BIKE_URBAN":
        riders["new"]["max_price"] = fare(10000, 4500, 250, *direct[0])
    else:
        private = fare(20000, 11000, 500, *direct[0])
        quote = int(private * 0.8 // 1000) * 1000
        riders["new"]["max_price"] = private if c.service_code == "CAR_URBAN_PRIVATE" else int((quote + 0.5 * (private - quote)) // 1000) * 1000
    stop_pts = {}
    added_pickups = 0
    if c.plan_id:
        rows = session.execute(text(
            "SELECT s.booking_id, s.kind, s.status, s.completed_at, ST_X(s.geom) x, ST_Y(s.geom) y, b.seat_count, "
            "b.quoted_price_cap_vnd, p.traveled_km_before_last_replan km, p.direct_distance_m dm, p.direct_duration_s ds, "
            "t.preferred_departure, t.budget_max FROM ride_stops s JOIN bookings b ON b.id = s.booking_id "
            "JOIN ride_participants p ON p.booking_id = s.booking_id JOIN trip_requests t ON t.id = b.request_id "
            "WHERE s.ride_plan_id = :p ORDER BY s.seq"), {"p": c.plan_id}).mappings().all()
        completed = sum(r["status"] == "COMPLETED" for r in rows)
        for r in rows:
            ref = str(r["booking_id"])
            stop_pts[(ref, r["kind"])] = (r["x"], r["y"])
            if r["status"] == "COMPLETED" and r["kind"] == "PICKUP":
                riders[ref] = {"onboard": True, "boarded": r["completed_at"]}
            riders.setdefault(ref, {"onboard": False})
            riders[ref] |= {"seats": r["seat_count"], "direct": (r["dm"], r["ds"]), "traveled": r["km"] * 1000,
                            "max_price": r["quoted_price_cap_vnd"], "budget": r["budget_max"],
                            "window": (r["preferred_departure"] + timedelta(minutes=5),
                                       r["preferred_departure"] + timedelta(minutes=20))}
        riders = {k: v for k, v in riders.items() if k == "new" or any(s[0] == k for s in c.insertion["chain"])}
        added_pickups = len(riders) - 1
        total_stops = completed + len(c.insertion["chain"])
        if total_stops > 8 or added_pickups > d["max_additional_pickups"]:
            bad.add("HC07")
    riders["new"]["budget"] = trip["budget_max"]
    pts = [(d["x"], d["y"])]
    for ref, kind in c.insertion["chain"]:
        pts.append(stop_pts.get((ref, kind)) or (trip["p"] if kind == "PICKUP" else trip["q"]))
    legs = osrm.legs(profile, pts)
    if legs is None:
        return bad | {"HC02"}, edge
    clock = dist = 0.0
    seats = sum(r["seats"] for r in riders.values() if r["onboard"])
    at = {}
    for (ref, kind), (lm, ls) in zip(c.insertion["chain"], legs, strict=True):
        if seats > d["capacity"]:
            bad.add("HC04")
        clock += ls
        dist += lm
        r = riders[ref]
        if kind == "PICKUP":
            clock = max(clock, (r["window"][0] - now).total_seconds())
            seats += r["seats"]
        else:
            seats -= r["seats"]
        at[(ref, kind)] = (clock, dist)
        clock += 60
    n = len(legs)
    for ref, r in riders.items():
        t_drop, m_drop = at[(ref, "DROPOFF")]
        if r["onboard"]:
            ride, inveh = r["traveled"] + m_drop, (now - r["boarded"]).total_seconds() + t_drop
        else:
            t_pick, m_pick = at[(ref, "PICKUP")]
            pick = now + timedelta(seconds=t_pick)
            if pick > r["window"][1] + timedelta(seconds=TOL_S * n):
                bad.add("HC03")
            elif pick > r["window"][1]:
                edge.add("HC03")
            ride, inveh = m_drop - m_pick, t_drop - t_pick
        direct_m, direct_s = r["direct"]
        max_inveh = direct_s * 1.5 + 600
        if inveh > max_inveh + TOL_S * n:
            bad.add("HC06")
        elif inveh > max_inveh:
            edge.add("HC06")
        if c.service_code == "CAR_URBAN_POOL" and direct_m:
            if ride > 1.3 * direct_m + TOL_M * n:
                bad.add("HC05")
            elif ride > 1.3 * direct_m:
                edge.add("HC05")
        if r.get("budget") is not None and r["max_price"] > r["budget"]:
            bad.add("HC08")
    return bad, edge


def make_world(session, rng: random.Random, n_drivers: int, n_plans: int, now: datetime, osrm: OsrmLegs) -> None:  # noqa: ANN001
    session.execute(text("TRUNCATE ride_stops, ride_participants, ride_candidates, candidate_runs, bookings, ride_plans, "
                         "driver_locations, vehicles, trip_requests, driver_profiles, users RESTART IDENTITY CASCADE"))
    for i in range(n_drivers):
        bike = i % 2 == 0
        fx.driver(session, *disk(rng, CENTER, 7), now, vehicle_type="BIKE" if bike else "CAR4",
                  pool=(not bike and rng.random() < 0.4), max_additional_pickups=rng.choice([2, 3]))
    for _ in range(n_plans):
        pos = disk(rng, CENTER, 4)
        car, vehicle = fx.driver(session, *pos, now, pool=True, max_additional_pickups=3)
        a_pick = disk(rng, pos, 2)
        a_drop = disk(rng, pos, 6)
        legs = osrm.legs("car", [a_pick, a_drop])
        so_far = osrm.legs("car", [a_pick, pos])
        if legs is None or so_far is None:
            continue
        rider = fx.user(session)
        a_trip = fx.trip(session, rider, a_pick, a_drop, now - timedelta(minutes=25), allowed=["CAR_URBAN_POOL"])
        fx.onboard_plan(session, car, vehicle, a_trip, rider, a_pick, a_drop, now - timedelta(minutes=8),
                        direct_m=legs[0][0], direct_s=legs[0][1], traveled_km=so_far[0][0] / 1000, cap_vnd=174000)
    session.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", default=str(ROOT / "docs" / "implementation" / "evidence" / "p2_benchmark.json"))
    ap.add_argument("--in-network", action="store_true", help="run inside the compose network (required for latency)")
    ap.add_argument("--configs", default="", help="subset, e.g. 200x10,200x20")
    args = ap.parse_args()
    env = dotenv()
    if args.in_network:
        urls = {"car": "http://osrm-car:5000", "motorbike": "http://osrm-motorbike:5000"}
        base = os.environ["DATABASE_URL"]
    else:
        urls = {"car": f"http://127.0.0.1:{env.get('OSRM_CAR_HOST_PORT', '5000')}",
                "motorbike": f"http://127.0.0.1:{env.get('OSRM_MOTORBIKE_HOST_PORT', '5001')}"}
        base = (f"postgresql+psycopg://{env.get('POSTGRES_USER')}:{env.get('POSTGRES_PASSWORD')}"
                f"@127.0.0.1:{env.get('POSTGRES_HOST_PORT', '5432')}/postgres")
    url = recreate(base)
    migrate(url)
    os.environ |= {"DATABASE_URL": url, "REDIS_URL": "redis://127.0.0.1:1/0", "OSRM_CAR_URL": urls["car"],
                   "OSRM_MOTORBIKE_URL": urls["motorbike"],
                   "CONFIG_BASELINE_PATH": str(ROOT / "config" / "mvp_config_baseline_v1.yaml"),
                   "JWT_SECRET": "bench-" + uuid.uuid4().hex, "SERVICE_AREA_VERSION": fx.VERSION}
    from app.core.settings import get_settings
    from app.modules.candidate.generator import generate
    from app.modules.routing.osrm import OsrmRoutingProvider
    from app.modules.routing.provider import Profile, RoutingPolicy
    from app.modules.trip.service import trip_snapshots

    settings = get_settings()
    engine = create_engine(url)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    fx.setup_reference_data(session)
    osrm = OsrmLegs(urls)
    report = {"label": "SYNTHETIC benchmark data on a throwaway database - local machine only",
              "network": "compose network (backend container)" if args.in_network else "Windows host via port proxy",
              "host": {"platform": platform.platform(), "processor": platform.processor(), "python": platform.python_version(),
                       "cpu_count": os.cpu_count()},
              "parameters": {"R_urban_m": 5000, "N_single": 15, "N_pool": 20, "k_max_stops": 8, "requests": args.requests,
                             "seed": args.seed, "tolerance_per_leg": {"s": TOL_S, "m": TOL_M}},
              "target": "R9 Section 77: PostGIS + 1 OSRM table p95 <= 300 ms; Section 79 P2: generation < 300 ms",
              "configs": []}
    try:
        wanted = {tuple(map(int, c.split("x"))) for c in args.configs.split(",") if c}
        for n_drivers, n_plans in [c for c in CONFIGS if not wanted or c in wanted]:
            rng = random.Random(f"{args.seed}-{n_drivers}-{n_plans}")
            now = datetime.now(UTC).replace(microsecond=0)
            make_world(session, rng, n_drivers, n_plans, now, osrm)
            stages: dict[str, list[float]] = {}
            stage_total: list[float] = []
            spatial_osrm: list[float] = []
            osrm_requests: list[int] = []
            feasible = violations = edges = 0
            by_code: dict[str, int] = {}
            edge_codes: dict[str, int] = {}
            rejected: dict[str, int] = {}
            samples: list[dict] = []
            provider = OsrmRoutingProvider({Profile.CAR: urls["car"], Profile.MOTORBIKE: urls["motorbike"]},
                                           settings.routing_timeout_s, RoutingPolicy(("ferry",), settings.routing_version),
                                           settings.osrm_max_table_size)
            for _ in range(args.requests):
                p = disk(rng, CENTER, 5)
                q = disk(rng, p, rng.uniform(2, 10))
                trip_id = fx.trip(session, fx.user(session), p, q, now)
                session.commit()
                snap = trip_snapshots(session, [trip_id])[trip_id]
                started = time.perf_counter()
                result = generate(session, settings, snap, provider, now)
                stage_total.append((time.perf_counter() - started) * 1000)
                for k, v in result.timings_ms.items():
                    stages.setdefault(k, []).append(v)
                spatial_osrm.append(result.timings_ms.get("postgis", 0) + result.timings_ms.get("osrm_wall", 0))
                osrm_requests.append(result.osrm_requests)
                for codes in result.rejections.values():
                    for code, k in codes.items():
                        rejected[code] = rejected.get(code, 0) + k
                trip = {"p": p, "q": q, "preferred_departure": now, "passenger_count": 1, "budget_max": None,
                        "allowed_service_codes": snap.allowed_service_codes}
                for c in result.candidates:
                    feasible += 1
                    bad, edge = verify(c, session, osrm, trip, now)
                    violations += bool(bad)
                    edges += bool(edge)
                    for code in bad:
                        by_code[code] = by_code.get(code, 0) + 1
                    if bad and len(samples) < 10:
                        samples.append({"codes": sorted(bad), "service": c.service_code, "source": c.source_type,
                                        "insertion": c.insertion, "audit": c.audit})
                    for code in edge:
                        edge_codes[code] = edge_codes.get(code, 0) + 1
            entry = {"drivers": n_drivers, "open_plans": n_plans,
                     "generation_total_ms": summary(stage_total),
                     "postgis_plus_osrm_ms": summary(spatial_osrm),
                     "stages_ms": {k: summary(v) for k, v in stages.items()},
                     "osrm_requests_per_run": sorted(set(osrm_requests)),
                     "candidates_feasible": feasible, "candidates_with_violation": violations,
                     "violations_by_code": by_code, "borderline_within_tolerance": edges, "borderline_by_code": edge_codes,
                     "rejections_by_code": rejected, "violation_samples": samples,
                     "meets_300ms_p95_total": (pct(stage_total, 95) or 0) < 300}
            report["configs"].append(entry)
            print(json.dumps({k: entry[k] for k in ("drivers", "open_plans", "candidates_feasible",
                                                    "candidates_with_violation", "borderline_within_tolerance")}),
                  "| total p95", entry["generation_total_ms"]["p95"], "| PostGIS+OSRM p95", entry["postgis_plus_osrm_ms"]["p95"],
                  "| osrm_car p95", entry["stages_ms"].get("osrm_car", {}).get("p95"),
                  "| constraints p95", entry["stages_ms"]["constraints"]["p95"], flush=True)
    finally:
        session.close()
        engine.dispose()
        drop(base)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8", newline="\n")
    print("written", args.out)


if __name__ == "__main__":
    main()
