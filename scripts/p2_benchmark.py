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

Modes: bench (latency per stage; --verify adds the independent checks of scripts/p2_verify.py),
explain (EXPLAIN (ANALYZE, BUFFERS) of every SQL statement of a generation run), cprofile.
Run it through scripts/p2_bench_run.sh, which stores each run in its own evidence folder
(run id, git commit, seed, workload, docker stats, exit code) and never overwrites one.
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

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, make_url, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

sys.path.insert(0, str(ROOT / "backend" / "tests"))
import p2_fixtures as fx  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from p2_verify import TOL_M, TOL_S, Osrm, check_plan, check_single_reject, verify_candidate  # noqa: E402

DB = "p2_bench"
CENTER = (105.8520, 21.0285)
CONFIGS = [(50, 0), (200, 0), (1000, 0), (200, 10), (200, 20), (1000, 20)]


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


HC_CONFIG = ("hc", 200, 20)  # constraint-stress workload (hardening directive section 4.1)


def make_world(session, rng: random.Random, n_drivers: int, n_plans: int, now: datetime, osrm: Osrm) -> None:  # noqa: ANN001
    """Workload of the 6 standard configurations - unchanged since the first run, so before /
    after compare the same world for the same seed."""
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


def make_world_hc(session, rng: random.Random, n_drivers: int, n_plans: int, now: datetime, osrm: Osrm) -> None:  # noqa: ANN001
    """Constraint-stress workload: plans with 1-3 riders (first rider onboard, others onboard or
    waiting, up to 5 stops ahead), driver detour limits (HC07), same-gender riders (HC11 - never
    satisfiable while no gender verification exists, P1-D6) and budgets on new trips (HC08)."""
    make_world(session, rng, n_drivers, 0, now, osrm)
    for _ in range(n_plans):
        pos = disk(rng, CENTER, 4)
        limit = rng.choice([None, None, (3.0, 10.0), (6.0, 15.0)])
        car, vehicle = fx.driver(session, *pos, now, pool=True, max_additional_pickups=3,
                                 detour_km=limit[0] if limit else None, detour_min=limit[1] if limit else None)
        riders: list[dict] = []
        ahead: list[tuple[int, str]] = []
        for k in range(rng.choice([1, 2, 2, 3])):
            onboard = k == 0 or rng.random() < 0.3
            pick = disk(rng, pos, 2 if onboard else 1.5)
            drop = disk(rng, pos, 6)
            legs = osrm.legs("car", [pick, drop])
            so_far = osrm.legs("car", [pick, pos]) if onboard else [(0.0, 0.0)]
            if legs is None or so_far is None:
                continue
            user = fx.user(session)
            trip_id = fx.trip(session, user, pick, drop, now - timedelta(minutes=25 if onboard else 2),
                              allowed=["CAR_URBAN_POOL"], same_gender=rng.random() < 0.2)
            riders.append({"user": user, "trip": trip_id, "pickup": pick, "dropoff": drop, "onboard": onboard,
                           "boarded": now - timedelta(minutes=8), "direct_m": legs[0][0], "direct_s": legs[0][1],
                           "traveled_km": so_far[0][0] / 1000, "cap_vnd": 174000})
            i = len(riders) - 1
            if onboard:
                ahead.insert(rng.randint(0, len(ahead)), (i, "DROPOFF"))
            else:
                j = rng.randint(0, len(ahead))
                ahead.insert(j, (i, "PICKUP"))
                ahead.insert(rng.randint(j + 1, len(ahead)), (i, "DROPOFF"))
        if riders and riders[0]["onboard"]:
            fx.plan(session, car, vehicle, riders, ahead)
    session.commit()


def capture_sql(engine):  # noqa: ANN001, ANN201
    from sqlalchemy import event

    captured: list[tuple[str, object]] = []

    def before(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001, ANN202
        captured.append((statement, parameters))

    event.listen(engine, "before_cursor_execute", before)
    return captured, lambda: event.remove(engine, "before_cursor_execute", before)


def stop_point(session, ref: str, kind: str, trip_id: uuid.UUID) -> tuple[float, float]:  # noqa: ANN001
    if ref == "new":
        col = "pickup_geom" if kind == "PICKUP" else "dropoff_geom"
        return tuple(session.execute(text(f"SELECT ST_X({col}), ST_Y({col}) FROM trip_requests WHERE id = :t"),
                                     {"t": trip_id}).one())
    return tuple(session.execute(text("SELECT ST_X(geom), ST_Y(geom) FROM ride_stops WHERE booking_id = :b AND kind = :k"),
                                 {"b": ref, "k": kind}).one())


def radius_check(session, osrm: Osrm, requests: list, now: datetime, name: str) -> str:  # noqa: ANN001
    """OD-P2-05: are feasible drivers lost by the 5 km PostGIS radius? For every request, the IDLE
    urban drivers within 12 km straight-line get their real ETA to P from ONE independent OSRM
    table per profile; a driver beyond 5 km is a potential false negative when it reaches P before
    the end of the pickup window AND (a) fewer than 15 drivers inside 5 km are in time, or (b) it is
    faster than the slowest of the 15 nearest inside 5 km (the list the generator keeps)."""
    import httpx

    out = {"requests": 0, "requests_with_case_a": 0, "requests_with_case_b": 0, "drivers_beyond_5km_in_time": 0,
           "by_profile": {}}
    for trip_id in requests:
        p = tuple(session.execute(text("SELECT ST_X(pickup_geom), ST_Y(pickup_geom) FROM trip_requests WHERE id = :t"),
                                  {"t": trip_id}).one())
        out["requests"] += 1
        hit_a = hit_b = False
        for profile, vt, window_s in (("motorbike", "BIKE", 15 * 60), ("car", "CAR4", 20 * 60)):
            rows = session.execute(text(
                "SELECT ST_X(dl.geom), ST_Y(dl.geom), ST_Distance(dl.geom::geography, "
                "ST_SetSRID(ST_MakePoint(:x, :y), 4326)::geography) d FROM driver_locations dl "
                "JOIN vehicles v ON v.id = dl.active_vehicle_id JOIN driver_profiles dp ON dp.user_id = dl.driver_id "
                "WHERE dl.availability = 'IDLE' AND v.vehicle_type = :vt AND dp.accepts_urban AND ST_DWithin("
                "dl.geom::geography, ST_SetSRID(ST_MakePoint(:x, :y), 4326)::geography, 12000) ORDER BY d"),
                {"x": p[0], "y": p[1], "vt": vt}).all()
            if not rows:
                continue
            pts = [(r[0], r[1]) for r in rows] + [p]
            path = ";".join(f"{x:.6f},{y:.6f}" for x, y in pts)
            body = httpx.get(f"{osrm.urls[profile]}/table/v1/driving/{path}",
                             params={"sources": ";".join(map(str, range(len(rows)))), "destinations": str(len(rows)),
                                     "annotations": "duration", "exclude": "ferry"},
                             headers={"Connection": "close"}, timeout=30).json()
            eta = [row[0] for row in body["durations"]]
            inside = [(r[2], e) for r, e in zip(rows, eta, strict=True) if r[2] <= 5000]
            kept = inside[:15]
            in_time_inside = [e for _, e in kept if e is not None and e <= window_s]
            beyond = [e for r, e in zip(rows, eta, strict=True) if r[2] > 5000 and e is not None and e <= window_s]
            stat = out["by_profile"].setdefault(profile, {"beyond_5km_in_time": 0, "case_a": 0, "case_b": 0})
            stat["beyond_5km_in_time"] += len(beyond)
            out["drivers_beyond_5km_in_time"] += len(beyond)
            if beyond and len(in_time_inside) < 15:
                stat["case_a"] += 1
                hit_a = True
            slowest = max((e for _, e in kept if e is not None), default=None)
            if beyond and slowest is not None and min(beyond) < slowest:
                stat["case_b"] += 1
                hit_b = True
        out["requests_with_case_a"] += hit_a
        out["requests_with_case_b"] += hit_b
    return f"===== {name}: radius check =====" + chr(10) + json.dumps(out, indent=2)


def bump(counter: dict, key: str, by: int = 1) -> None:
    counter[key] = counter.get(key, 0) + by


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--in-network", action="store_true", help="run inside the compose network (required for latency)")
    ap.add_argument("--configs", default="", help="subset, e.g. 200x10,200x20,hc")
    ap.add_argument("--mode", choices=["bench", "explain", "cprofile", "radius"], default="bench")
    ap.add_argument("--verify", action="store_true", help="independent re-check of every candidate and rejection")
    ap.add_argument("--analyze", action="store_true",
                    help="ANALYZE after loading the synthetic world (planner statistics, as autovacuum keeps them in a "
                         "running database); runs without it measure a freshly loaded, never-analysed database")
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
    from app.modules.candidate.service import OFFERABLE_PRICING_CHECKS, persist
    from app.modules.routing.osrm import OsrmRoutingProvider
    from app.modules.routing.provider import Profile, RoutingPolicy
    from app.modules.trip.service import trip_snapshots

    settings = get_settings()
    engine = create_engine(url)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    fx.setup_reference_data(session)
    osrm = Osrm(urls)
    policy = RoutingPolicy(("ferry",), settings.routing_version)
    report = {"run_id": args.run_id, "mode": args.mode, "verify": args.verify, "analyze": args.analyze,
              "label": "SYNTHETIC benchmark data on a throwaway database - local machine only",
              "network": "compose network (backend container)" if args.in_network else "Windows host via port proxy",
              "started_utc": datetime.now(UTC).isoformat(),
              "host": {"platform": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count()},
              "parameters": {"R_urban_m": 5000, "N_single": 15, "N_pool": 20, "k_max_stops": 8, "requests": args.requests,
                             "seed": args.seed, "tolerance_per_leg": {"s": TOL_S, "m": TOL_M}},
              "target": "R9 Section 77: PostGIS + 1 OSRM table p95 <= 300 ms; Section 79 P2: generation < 300 ms",
              "configs": []}
    wanted = [c for c in args.configs.split(",") if c]
    workloads = [("std", d, p) for d, p in CONFIGS if not wanted or f"{d}x{p}" in wanted]
    if not wanted or "hc" in wanted:
        workloads.append(HC_CONFIG)
    texts: list[str] = []
    try:
        for kind, n_drivers, n_plans in workloads:
            rng = random.Random(f"{args.seed}-{n_drivers}-{n_plans}" + ("-hc" if kind == "hc" else ""))
            now = datetime.now(UTC).replace(microsecond=0)
            (make_world_hc if kind == "hc" else make_world)(session, rng, n_drivers, n_plans, now, osrm)
            if args.analyze:
                session.execute(text("ANALYZE"))
                session.commit()
            provider = OsrmRoutingProvider({Profile.CAR: urls["car"], Profile.MOTORBIKE: urls["motorbike"]},
                                           settings.routing_timeout_s, policy, settings.osrm_max_table_size)
            requests = []
            for _ in range(args.requests):
                p = disk(rng, CENTER, 5)
                q = disk(rng, p, rng.uniform(2, 10))
                if kind == "hc":
                    sg = rng.random() < 0.2
                    budget = rng.choice([None, None, None, 90000, 150000])
                    requests.append(fx.trip(session, fx.user(session), p, q, now, same_gender=sg, budget_max=budget))
                else:
                    requests.append(fx.trip(session, fx.user(session), p, q, now))
            session.commit()
            name = f"{n_drivers}x{n_plans}" + ("-hc" if kind == "hc" else "")
            if args.mode == "explain":
                captured, stop = capture_sql(engine)
                for trip_id in requests[:3]:
                    generate(session, settings, trip_snapshots(session, [trip_id])[trip_id], provider, now)
                stop()
                texts.append(f"===== {name}: {len(captured) / 3:.1f} SQL statements per generation run "
                             "(incl. the trip snapshot read before generate) =====")
                seen = set()
                for stmt, params in captured:
                    if stmt in seen:
                        continue
                    seen.add(stmt)
                    with engine.connect() as conn:
                        rows = conn.exec_driver_sql("EXPLAIN (ANALYZE, BUFFERS) " + stmt, params).all()
                    texts.append("-- " + " ".join(stmt.split())[:500])
                    texts += [r[0] for r in rows]
                    texts.append("")
                continue
            if args.mode == "radius":
                texts.append(radius_check(session, osrm, requests, now, name))
                continue
            if args.mode == "cprofile":
                import cProfile
                import io
                import pstats

                prof = cProfile.Profile()
                for trip_id in requests:
                    snap = trip_snapshots(session, [trip_id])[trip_id]
                    prof.enable()
                    generate(session, settings, snap, provider, now)
                    prof.disable()
                for key in ("cumulative", "tottime"):
                    buf = io.StringIO()
                    pstats.Stats(prof, stream=buf).sort_stats(key).print_stats(40)
                    texts.append(f"===== {name}: {len(requests)} runs, sorted by {key} =====\n{buf.getvalue()}")
                continue

            stages: dict[str, list[float]] = {}
            totals: list[float] = []
            with_persist: list[float] = []
            osrm_requests: list[int] = []
            errors: dict[str, int] = {}
            rejected: dict[str, int] = {}
            ver: dict = {"candidates_checked": 0, "with_violation": 0, "violations_by_code": {}, "borderline_by_code": {},
                         "pending_p3": 0, "pending_p3_offerable": 0, "single_rejections": {}, "plan_checks": {},
                         "sf_p2_15_default_routing": {"pool_candidates": 0, "would_violate": 0, "by_code": {}},
                         "samples": []}
            ratios: list[float] = []
            for trip_id in requests:
                snap = trip_snapshots(session, [trip_id])[trip_id]
                started = time.perf_counter()
                try:
                    result = generate(session, settings, snap, provider, now)
                except Exception as exc:  # noqa: BLE001 - counted and reported, never hidden
                    bump(errors, type(exc).__name__)
                    session.rollback()
                    continue
                totals.append((time.perf_counter() - started) * 1000)
                t_persist = time.perf_counter()
                persist(session, trip_id, policy, fx.VERSION, result)
                persist_ms = (time.perf_counter() - t_persist) * 1000
                with_persist.append(totals[-1] + persist_ms)
                timings = dict(result.timings_ms) | {"persist": persist_ms}
                timings["postgis"] = timings.get("postgis_drivers", 0) + timings.get("plan_lookup", 0)
                timings["postgis_plus_osrm"] = timings["postgis"] + timings.get("osrm_wall", 0)
                for k, v in timings.items():
                    stages.setdefault(k, []).append(v)
                osrm_requests.append(result.osrm_requests)
                for codes in result.rejections.values():
                    for code, k in codes.items():
                        bump(rejected, code, k)
                if not args.verify:
                    continue
                produced = {(c.service_code, c.driver_id) for c in result.candidates if c.plan_id is None}
                for c in result.candidates:
                    ver["candidates_checked"] += 1
                    if c.pricing_check == "PENDING_P3":
                        ver["pending_p3"] += 1
                        ver["pending_p3_offerable"] += int(c.pricing_check in OFFERABLE_PRICING_CHECKS)
                    bad, edge = verify_candidate(c, session, osrm, trip_id, now)
                    ver["with_violation"] += int(bool(bad))
                    for code in bad:
                        bump(ver["violations_by_code"], code)
                    for code in edge:
                        bump(ver["borderline_by_code"], code)
                    if bad and len(ver["samples"]) < 10:
                        ver["samples"].append({"codes": sorted(bad), "service": c.service_code, "source": c.source_type,
                                               "insertion": c.insertion, "audit": c.audit})
                    if c.service_code == "CAR_URBAN_POOL":
                        sf = ver["sf_p2_15_default_routing"]
                        sf["pool_candidates"] += 1
                        bad_default, _ = verify_candidate(c, session, osrm, trip_id, now, continue_straight=None)
                        extra = bad_default - bad
                        sf["would_violate"] += int(bool(extra))
                        for code in extra:
                            bump(sf["by_code"], code)
                        start = tuple(session.execute(text("SELECT ST_X(geom), ST_Y(geom) FROM driver_locations "
                                                           "WHERE driver_id = :d"), {"d": c.driver_id}).one())
                        pts = [start] + [stop_point(session, r, k, trip_id) for r, k in c.insertion["chain"]]
                        table_like, default = osrm.legs("car", pts), osrm.legs("car", pts, None)
                        if table_like and default:
                            ratios.append(sum(x[0] for x in default) / max(1.0, sum(x[0] for x in table_like)))
                for service, driver_id in result.evaluated_drivers:
                    if (service, driver_id) not in produced:
                        bump(ver["single_rejections"], check_single_reject(session, osrm, service, driver_id, trip_id, now))
                deltas = {c.plan_id: c.insertion["delta_cost_vnd"] for c in result.candidates if c.plan_id}
                for plan_id in result.evaluated_plans:
                    bump(ver["plan_checks"], check_plan(session, osrm, plan_id, trip_id, now, deltas.get(plan_id)))
            if args.verify:
                sf = ver["sf_p2_15_default_routing"]
                sf["chain_distance_ratio_default_over_table"] = summary(ratios)
                sf["chains_longer_than_1pct"] = sum(r > 1.01 for r in ratios)
            entry = {"config": name, "drivers": n_drivers, "open_plans": n_plans, "requests": len(requests),
                     "errors": errors, "generation_total_ms": summary(totals),
                     "generation_plus_persist_ms": summary(with_persist),
                     "stages_ms": {k: summary(v) for k, v in sorted(stages.items())},
                     "osrm_requests_per_run": sorted(set(osrm_requests)), "rejections_by_code": rejected,
                     "meets_300ms_p95_total": (pct(totals, 95) or 0) < 300}
            if args.verify:
                entry["verification"] = ver
            report["configs"].append(entry)
            s = entry["stages_ms"]
            print(name, "| total p50/p95/p99", entry["generation_total_ms"]["p50"], entry["generation_total_ms"]["p95"],
                  entry["generation_total_ms"]["p99"], "| postgis p95", s["postgis"]["p95"], "| osrm_car p95",
                  s.get("osrm_car", {}).get("p95"), "| step3 p95", s["constraints"]["p95"], "| errors", errors,
                  ("| viol " + str(ver["violations_by_code"]) + " plans " + str(ver["plan_checks"])
                   + " singles " + str(ver["single_rejections"])) if args.verify else "", flush=True)
    finally:
        session.close()
        engine.dispose()
        drop(base)
    report["finished_utc"] = datetime.now(UTC).isoformat()
    out = Path(args.out)
    if args.mode == "bench":
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8", newline="\n")
    else:
        out.write_text("\n".join(texts) + "\n", encoding="utf-8", newline="\n")
    print("written", out)


if __name__ == "__main__":
    main()
