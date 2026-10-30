"""Candidate generation for the three urban services (Revision 9 Sections 35.1, 35.2).

    1. PostGIS: online IDLE drivers of the right vehicle within R_urban of P, nearest
       N_single per service (BIKE, CAR4; CAR4 pool-enabled for branch B), and the open
       pool plans whose vehicle is within R_pool of P, filtered by direction and free
       seats, nearest N_pool (branch A).
    2. ONE OSRM table per profile (Section 34, P2-04; P2 plan OD-P2-01): `motorbike` for
       the bike drivers, `car` for every car node - idle drivers, plan vehicles, the
       stops ahead of them, P and Q. The two requests run in parallel.
    3. Every candidate - a new vehicle is an insertion into an empty plan - goes through
       pooling.insertion (Section 36) and candidate.constraints.check_all: the 11 hard
       constraints for every rider, with table look-ups only.

Branch A candidates carry pricing_check = PENDING_P3 (steps 4-5 of Section 36 are Phase 3;
P2 plan OD-P2-04) and are logged, never offered.
"""

import math
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.config_baseline import get_config_baseline
from app.core.settings import Settings
from app.modules.booking import service as booking_service
from app.modules.candidate.constraints import EXISTING_POOL_PLAN, NEW_SINGLE_VEHICLE, DriverState
from app.modules.driver import service as driver_service
from app.modules.identity import service as identity_service
from app.modules.pooling import repository as plans
from app.modules.pooling.insertion import DROPOFF, PICKUP, InsertionReport, Params, PlanState, RiderSpec, Stop, insert
from app.modules.pricing import service as pricing_service
from app.modules.pricing.tariff import distance_time_fare, pool_quote
from app.modules.routing.provider import Lonlat, Matrix, Profile, RoutingProvider
from app.modules.trip import rules as trip_rules
from app.modules.trip.service import TripSnapshot, trip_snapshots

URBAN = ("BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL")
# Section 35.1 steps 2-3 (values stated in the text, not in the Baseline YAML).
R_URBAN_M = 5000.0
N_SINGLE = 15
# P2 plan OD-P2-05: Revision 9 gives no number for R_pool; R_urban is used.
R_POOL_M = R_URBAN_M
# Section 35.2 step 2.
MAX_HEADING_DEG = 60.0
DEFAULT_DETOUR_RATIO = 0.30  # Section 6


@dataclass
class Candidate:
    service_code: str
    source_type: str
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID | None
    plan_id: uuid.UUID | None
    plan_version: int | None
    seat_count: int
    pickup_eta_s: float
    direct_distance_m: float
    direct_duration_s: float
    private_fare_vnd: int | None
    expected_price_vnd: int | None
    pool_quote_vnd: int | None
    pool_unmatched_vnd: int | None
    pricing_check: str
    insertion: dict[str, Any]
    audit: dict[str, Any]


@dataclass
class RunResult:
    status: str
    candidates: list[Candidate] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
    counts: dict[str, Any] = field(default_factory=dict)
    rejections: dict[str, dict[str, int]] = field(default_factory=dict)
    osrm_requests: int = 0
    error: str | None = None
    # Instrumentation only (not stored): what was evaluated, so an independent checker can
    # confirm that every rejection was right.
    evaluated_drivers: list[tuple[str, uuid.UUID]] = field(default_factory=list)
    evaluated_plans: list[uuid.UUID] = field(default_factory=list)


def _state(d: driver_service.DriverCandidate) -> DriverState:
    return DriverState(driver_id=d.driver_id, availability=d.availability, location_age_s=d.location_age_s,
                       kyc_status=d.kyc_status, accepts_urban=d.accepts_urban, pool_enabled=d.pool_enabled,
                       accepts_intercity=d.accepts_intercity, max_additional_pickups=d.max_additional_pickups,
                       max_driver_detour_km=d.max_driver_detour_km, max_driver_detour_min=d.max_driver_detour_min,
                       vehicle_id=d.vehicle_id, vehicle_type=d.vehicle_type, capacity=d.capacity,
                       vehicle_active=d.vehicle_active)


def pickup_window(trip: TripSnapshot, service: str, baseline: dict[str, Any]) -> tuple[datetime, datetime]:
    """P2 plan OD-P2-03. NOW: Section 2.2 pickup window after T_preferred, intersected with
    the rider's own [T_earliest, T_latest]; SCHEDULED without a window: [T_preferred,
    T_preferred + width of the NOW window]."""
    lo_min, hi_min = baseline["bike_urban" if service == "BIKE_URBAN" else "car_urban"]["now_pickup_window_min"]
    pref = trip.preferred_departure
    if trip.booking_type == "NOW":
        lo, hi = pref + timedelta(minutes=lo_min), pref + timedelta(minutes=hi_min)
        if trip.earliest_departure:
            lo = max(lo, trip.earliest_departure)
        if trip.latest_departure:
            hi = min(hi, trip.latest_departure)
        return lo, hi
    lo = trip.earliest_departure or pref
    return lo, trip.latest_departure or lo + timedelta(minutes=hi_min - lo_min)


def booking_time_ok(trip: TripSnapshot, service: str, baseline: dict[str, Any]) -> tuple[bool, str]:
    """Constraint 9: the Section 2.2 lead-time rule of the service, re-checked."""
    w = trip_rules.service_windows(baseline)[service]
    lead = trip.preferred_departure - trip.created_at
    ok = w.min_lead <= lead <= w.max_lead and service in trip.allowed_service_codes
    return ok, "" if ok else f"lead time {lead} outside [{w.min_lead}, {w.max_lead}] or service not allowed"


def _bearing(a: Lonlat, b: Lonlat) -> float:
    lat = math.radians((a[1] + b[1]) / 2)
    return math.degrees(math.atan2(b[1] - a[1], (b[0] - a[0]) * math.cos(lat)))


def _heading_ok(plan_pts: list[Lonlat], p: Lonlat, q: Lonlat) -> bool:
    """Section 35.2 step 2: heading difference < 60 degrees OR bounding boxes intersect."""
    diff = abs((_bearing(plan_pts[0], plan_pts[-1]) - _bearing(p, q) + 180) % 360 - 180)
    if diff < MAX_HEADING_DEG:
        return True
    xs, ys = [x for x, _ in plan_pts], [y for _, y in plan_pts]
    return not (max(p[0], q[0]) < min(xs) or min(p[0], q[0]) > max(xs)
                or max(p[1], q[1]) < min(ys) or min(p[1], q[1]) > max(ys))


def _square(m: Matrix, src: list[int], dst: list[int], n: int) -> tuple[list[list[float | None]], list[list[float | None]]]:
    D: list[list[float | None]] = [[None] * n for _ in range(n)]
    T: list[list[float | None]] = [[None] * n for _ in range(n)]
    for i, a in enumerate(src):
        for j, b in enumerate(dst):
            D[a][b], T[a][b] = m.distance_m[i][j], m.duration_s[i][j]
    return D, T


@dataclass
class _Nodes:
    points: list[Lonlat] = field(default_factory=list)

    def add(self, p: Lonlat) -> int:
        self.points.append(p)
        return len(self.points) - 1


def generate(session: Session, settings: Settings, trip: TripSnapshot, provider: RoutingProvider,
             now: datetime) -> RunResult:
    t_start = time.perf_counter()
    baseline = get_config_baseline()
    car_urban = baseline["car_urban"]
    services = [s for s in URBAN if s in trip.allowed_service_codes]
    result = RunResult(status="OK", counts={"services": services,
                                            "not_in_p2": [s for s in trip.allowed_service_codes if s not in URBAN]})
    if not services:
        result.timings_ms["total"] = (time.perf_counter() - t_start) * 1000
        return result
    params = Params(dwell_s=float(car_urban["stop_dwell_time_s"]), k_max_stops=int(car_urban["k_max_stops"]),
                    location_stale_s=settings.location_stale_s, per_km_vnd=float(car_urban["per_km_vnd"]),
                    per_min_vnd=float(car_urban["per_min_vnd"]), stop_fee_vnd=float(car_urban["extra_stop_fee_vnd"]))
    n_pool = int(car_urban["n_pool_max_candidates"])
    p_pt, q_pt = trip.pickup, trip.dropoff

    # ---- 1. PostGIS ---------------------------------------------------------
    t0 = time.perf_counter()
    lon, lat = p_pt
    stale = settings.location_stale_s
    near = driver_service.nearby_idle_drivers(session, lon, lat, R_URBAN_M, N_SINGLE, now, stale)
    bikes = near["BIKE"] if "BIKE_URBAN" in services else []
    cars: dict[uuid.UUID, driver_service.DriverCandidate] = {}
    if "CAR_URBAN_PRIVATE" in services:
        cars |= {d.driver_id: d for d in near["CAR4"]}
    pool_b: set[uuid.UUID] = set()
    if "CAR_URBAN_POOL" in services:
        cars |= {d.driver_id: d for d in near["CAR4_POOL"]}
        pool_b = {d.driver_id for d in near["CAR4_POOL"]}
    result.timings_ms["postgis_drivers"] = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    plan_recs: list[tuple[plans.PlanRecord, driver_service.DriverCandidate]] = []
    if "CAR_URBAN_POOL" in services:
        by_driver = plans.open_plan_drivers(session)
        snaps = driver_service.driver_snapshots(session, list(by_driver), lon, lat, now)
        near = sorted((s for s in snaps.values() if s.distance_m <= R_POOL_M and s.pool_enabled
                       and s.kyc_status == "VERIFIED"), key=lambda s: s.distance_m)
        records = {r.plan_id: r for r in plans.plan_records(session, [by_driver[s.driver_id] for s in near])}
        for s in near:
            rec = records[by_driver[s.driver_id]]
            ahead = [x for x in rec.stops if x.status == "PLANNED"]
            if not ahead or not _heading_ok([(s.lon, s.lat)] + [(x.lon, x.lat) for x in ahead], p_pt, q_pt):
                continue
            plan_recs.append((rec, s))
            if len(plan_recs) == n_pool:
                break
    result.timings_ms["plan_lookup"] = (time.perf_counter() - t0) * 1000
    result.counts |= {"bike_drivers": len(bikes), "car_drivers": len(cars), "pool_b_drivers": len(pool_b),
                      "pool_plans": len(plan_recs)}

    # ---- rider data of the plans (constraints of every old rider) ----------
    t0 = time.perf_counter()
    booking_ids = [x.booking_id for rec, _ in plan_recs for x in rec.stops if x.status == "PLANNED"]
    views = booking_service.booking_views(session, booking_ids)
    trips = trip_snapshots(session, [v.request_id for v in views.values()])
    genders = identity_service.verified_genders(session, [trip.user_id] + [v.user_id for v in views.values()])
    result.timings_ms["plan_riders"] = (time.perf_counter() - t0) * 1000

    # ---- 2. one table per profile, in parallel ------------------------------
    t0 = time.perf_counter()
    bike_nodes, car_nodes = _Nodes(), _Nodes()
    bike_drv = {d.driver_id: bike_nodes.add((d.lon, d.lat)) for d in bikes}
    bp, bq = bike_nodes.add(p_pt), bike_nodes.add(q_pt)
    car_drv = {d.driver_id: car_nodes.add((d.lon, d.lat)) for d in cars.values()}
    plan_nodes: dict[uuid.UUID, tuple[int, list[tuple[plans.StopRecord, int]]]] = {}
    for rec, s in plan_recs:
        curr = car_nodes.add((s.lon, s.lat))
        plan_nodes[rec.plan_id] = (curr, [(x, car_nodes.add((x.lon, x.lat))) for x in rec.stops if x.status == "PLANNED"])
    cp, cq = car_nodes.add(p_pt), car_nodes.add(q_pt)

    def bike_table() -> tuple[list, list] | None:
        if not bikes:
            return None
        src = list(bike_drv.values()) + [bp]
        m = provider.matrix(Profile.MOTORBIKE, [bike_nodes.points[i] for i in src],
                            [bike_nodes.points[i] for i in (bp, bq)])
        result.timings_ms["osrm_motorbike"] = m.stats.get("osrm_ms", 0.0)
        result.counts["motorbike_matrix"] = [m.stats.get("sources"), m.stats.get("destinations")]
        t_sq = time.perf_counter()
        out = _square(m, src, [bp, bq], len(bike_nodes.points))
        result.timings_ms["convert_motorbike"] = m.stats.get("convert_ms", 0.0) + (time.perf_counter() - t_sq) * 1000
        return out

    def car_table() -> tuple[list, list] | None:
        if not cars and not plan_recs:
            return None
        if not plan_recs:  # Section 35.1 step 4: [drivers, P] x [P, Q]
            src, dst = list(car_drv.values()) + [cp], [cp, cq]
        else:
            # Section 34 / 35.2 step 4: one table over every car node as origin. Destinations are
            # the nodes a vehicle is ever routed TO - the stops ahead of each plan, P and Q; idle
            # drivers and plan vehicles (S_curr) are origins only. Every cell the insertion reads
            # has its destination in this set (test_insertion_reads_only_stop_destinations), so
            # the answer is the same as the full square, with fewer cells for OSRM to compute.
            src = list(range(len(car_nodes.points)))
            dst = [node for _, stops in plan_nodes.values() for _, node in stops] + [cp, cq]
        m = provider.matrix(Profile.CAR, [car_nodes.points[i] for i in src], [car_nodes.points[i] for i in dst])
        result.timings_ms["osrm_car"] = m.stats.get("osrm_ms", 0.0)
        result.timings_ms["osrm_car_http"] = m.stats.get("http_ms", 0.0)
        result.timings_ms["osrm_car_json"] = m.stats.get("json_ms", 0.0)
        result.counts["car_matrix"] = [m.stats.get("sources"), m.stats.get("destinations"), m.stats.get("coordinates")]
        t_sq = time.perf_counter()
        out = _square(m, src, dst, len(car_nodes.points))
        result.timings_ms["convert_car"] = m.stats.get("convert_ms", 0.0) + (time.perf_counter() - t_sq) * 1000
        return out

    with ThreadPoolExecutor(max_workers=2) as pool:
        bike_future, car_future = pool.submit(bike_table), pool.submit(car_table)
        bike_m, car_m = bike_future.result(), car_future.result()
    result.timings_ms["osrm_wall"] = (time.perf_counter() - t0) * 1000
    result.osrm_requests = int(bike_m is not None) + int(car_m is not None)

    # ---- 3. constraints / insertion ----------------------------------------
    t0 = time.perf_counter()
    version = baseline["pricing_version"]
    car_section = pricing_service.active_sections(session, "CAR_URBAN_PRIVATE", version)["car_urban"]
    bike_section = pricing_service.active_sections(session, "BIKE_URBAN", version)["bike_urban"] if bike_m else None
    result.timings_ms["pricing_params"] = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    ins_stats: dict[str, float] = {}
    t_record = 0.0
    rej: dict[str, Counter] = {s: Counter() for s in services}
    # Depend on the trip and the service only - computed once per service, not once per driver.
    booking_time = {s: booking_time_ok(trip, s, baseline) for s in services}
    riders_by_service: dict[tuple[str, int], RiderSpec] = {}

    def new_rider(service: str, D: list, T: list, p: int, q: int, private_fare: int | None) -> RiderSpec:
        key = (service, id(D))
        if key not in riders_by_service:
            riders_by_service[key] = _new_rider(service, D, T, p, q, private_fare)
        return riders_by_service[key]

    def _new_rider(service: str, D: list, T: list, p: int, q: int, private_fare: int | None) -> RiderSpec:
        d_m, d_s = D[p][q], T[p][q]
        direct_m, direct_s = (d_m or 0.0), (d_s or 0.0)
        if service == "BIKE_URBAN":
            max_price = distance_time_fare(bike_section, direct_m / 1000, direct_s / 60)  # type: ignore[arg-type]
        elif service == "CAR_URBAN_PRIVATE":
            max_price = private_fare
        else:
            max_price = pool_quote(car_section, private_fare).unmatched  # type: ignore[arg-type]
        return RiderSpec(
            ref="new", seats=trip.passenger_count, onboard=False, pickup_window=pickup_window(trip, service, baseline),
            actual_pickup=None, traveled_m=0.0, direct_distance_m=direct_m, direct_duration_s=direct_s,
            max_detour_ratio=trip.max_passenger_detour_ratio or DEFAULT_DETOUR_RATIO,
            max_in_vehicle_s=float(trip.max_in_vehicle_time_s) if trip.max_in_vehicle_time_s else
            direct_s * baseline["in_vehicle_time_default"]["direct_duration_multiplier"]
            + baseline["in_vehicle_time_default"]["additive_buffer_min"] * 60,
            latest_arrival=trip.latest_arrival, max_price_vnd=max_price, budget_max_vnd=trip.budget_max,
            walk_m=0, max_walk_m=trip.max_walk_m or 0, same_gender=trip.same_gender_coride,
            verified_gender=genders.get(trip.user_id))

    def record(service: str, source: str, d: driver_service.DriverCandidate, rep: InsertionReport,
               D: list, T: list, start: int, p: int, q: int, private_fare: int | None,
               plan: plans.PlanRecord | None) -> None:
        nonlocal t_record
        t_rec = time.perf_counter()
        rej[service].update(rep.rejections)
        best = rep.best
        if best is None:
            return
        new = next(r for r in best.evaluation.riders if r.ref == "new")
        quote = pool_quote(car_section, private_fare) if service == "CAR_URBAN_POOL" and private_fare else None
        result.candidates.append(Candidate(
            service_code=service, source_type=source, driver_id=d.driver_id, vehicle_id=d.vehicle_id,
            plan_id=plan.plan_id if plan else None, plan_version=plan.plan_version if plan else None,
            seat_count=trip.passenger_count, pickup_eta_s=float(T[start][p] or 0.0),
            direct_distance_m=float(D[p][q] or 0.0), direct_duration_s=float(T[p][q] or 0.0),
            private_fare_vnd=private_fare, expected_price_vnd=new.max_price_vnd if service != "CAR_URBAN_POOL" else None,
            pool_quote_vnd=quote.quote if quote else None, pool_unmatched_vnd=quote.unmatched if quote else None,
            pricing_check=best.pricing_check if source == EXISTING_POOL_PLAN else "COMPLETE",
            insertion={"p_idx": best.p_idx, "q_idx": best.q_idx,
                       "chain": [[s.ref, s.kind] for s in best.chain],
                       "segment_loads": list(best.evaluation.segment_loads),
                       "planned_pickup": new.planned_pickup.isoformat() if new.planned_pickup else None,
                       "planned_dropoff": new.planned_dropoff.isoformat(),
                       "added_distance_m": round(best.added_distance_m, 1),
                       "added_duration_s": round(best.added_duration_s, 1),
                       "delta_cost_vnd": round(best.delta_cost_vnd, 1)},
            audit={"checked": "HC01-HC11", "riders": [
                {"ref": r.ref, "onboard": r.onboard, "planned_pickup": r.planned_pickup.isoformat() if r.planned_pickup else None,
                 "window": [w.isoformat() for w in r.pickup_window] if r.pickup_window else None,
                 "in_vehicle_s": round(r.in_vehicle_s, 1), "max_in_vehicle_s": round(r.max_in_vehicle_s, 1),
                 "detour": round((r.ride_distance_m - r.direct_distance_m) / r.direct_distance_m, 4)
                 if r.direct_distance_m else 0.0, "max_detour": r.max_detour_ratio,
                 "max_price_vnd": r.max_price_vnd, "budget_max_vnd": r.budget_max_vnd}
                for r in best.evaluation.riders]}))
        t_record += time.perf_counter() - t_rec

    if bike_m is not None:
        D, T = bike_m
        for d in bikes:
            start = bike_drv[d.driver_id]
            state = PlanState(None, None, _state(d), start, now, 0, (), ())
            rider = new_rider("BIKE_URBAN", D, T, bp, bq, None)
            result.evaluated_drivers.append(("BIKE_URBAN", d.driver_id))
            rep = insert(state, rider, bp, bq, D, T, "BIKE_URBAN", NEW_SINGLE_VEHICLE,
                         booking_time["BIKE_URBAN"], params, stats=ins_stats)
            record("BIKE_URBAN", NEW_SINGLE_VEHICLE, d, rep, D, T, start, bp, bq, None, None)
    if car_m is not None:
        D, T = car_m
        direct_m, direct_s = D[cp][cq], T[cp][cq]
        private = (distance_time_fare(car_section, direct_m / 1000, direct_s / 60)
                   if direct_m is not None and direct_s is not None else None)
        for d in cars.values():
            start = car_drv[d.driver_id]
            for service in ("CAR_URBAN_PRIVATE", "CAR_URBAN_POOL"):
                if service not in services or (service == "CAR_URBAN_POOL" and d.driver_id not in pool_b):
                    continue
                state = PlanState(None, None, _state(d), start, now, 0, (), ())
                result.evaluated_drivers.append((service, d.driver_id))
                rep = insert(state, new_rider(service, D, T, cp, cq, private), cp, cq, D, T, service,
                             NEW_SINGLE_VEHICLE, booking_time[service], params, stats=ins_stats)
                record(service, NEW_SINGLE_VEHICLE, d, rep, D, T, start, cp, cq, private, None)
        t_pool = time.perf_counter()
        for rec, s in plan_recs:
            curr, ahead = plan_nodes[rec.plan_id]
            state = _plan_state(rec, s, curr, ahead, views, trips, genders, baseline, now)
            if state is None:
                rej["CAR_URBAN_POOL"]["PLAN_DATA_INCOMPLETE"] += 1
                continue
            result.evaluated_plans.append(rec.plan_id)
            rep = insert(state, new_rider("CAR_URBAN_POOL", D, T, cp, cq, private), cp, cq, D, T, "CAR_URBAN_POOL",
                         EXISTING_POOL_PLAN, booking_time["CAR_URBAN_POOL"], params,
                         stats=ins_stats)
            record("CAR_URBAN_POOL", EXISTING_POOL_PLAN, s, rep, D, T, curr, cp, cq, private, rec)
        result.timings_ms["insertion_pool_plans"] = (time.perf_counter() - t_pool) * 1000
    # "constraints" = everything of step 3 (insertion + hard constraints + candidate records), kept
    # under its old name for the before / after comparison; its parts are listed beside it.
    result.timings_ms["constraints"] = (time.perf_counter() - t0) * 1000
    result.timings_ms["check_all"] = ins_stats.get("check_all_s", 0.0) * 1000
    result.timings_ms["candidate_records"] = t_record * 1000
    result.counts["options_checked"] = int(ins_stats.get("options_checked", 0))
    result.rejections = {s: dict(c) for s, c in rej.items()}
    result.counts["feasible"] = dict(Counter(c.service_code for c in result.candidates))
    result.timings_ms["total"] = (time.perf_counter() - t_start) * 1000
    return result


def _plan_state(rec: plans.PlanRecord, s: driver_service.DriverCandidate, curr: int,
                ahead: list[tuple[plans.StopRecord, int]], views: dict, trips: dict, genders: dict,
                baseline: dict[str, Any], now: datetime) -> PlanState | None:
    """Section 36 input: S_curr = the vehicle position, the stops ahead and every rider still
    in the plan (onboard when its pickup is behind the vehicle)."""
    completed_pickups = {x.booking_id: x.completed_at for x in rec.stops if x.kind == PICKUP and x.status == "COMPLETED"}
    riders = []
    for booking_id in dict.fromkeys(x.booking_id for x, _ in ahead):
        view, direct = views.get(booking_id), rec.direct.get(booking_id)
        trip = trips.get(view.request_id) if view else None
        if view is None or trip is None or direct is None:
            return None  # incomplete plan data: never guess an old rider's constraints
        onboard = booking_id in completed_pickups
        defaults = baseline["in_vehicle_time_default"]
        riders.append(RiderSpec(
            ref=str(booking_id), seats=view.seat_count, onboard=onboard,
            pickup_window=None if onboard else pickup_window(trip, "CAR_URBAN_POOL", baseline),
            actual_pickup=completed_pickups.get(booking_id), traveled_m=rec.traveled_m.get(booking_id, 0.0),
            direct_distance_m=direct[0], direct_duration_s=direct[1],
            max_detour_ratio=trip.max_passenger_detour_ratio or DEFAULT_DETOUR_RATIO,
            max_in_vehicle_s=float(trip.max_in_vehicle_time_s) if trip.max_in_vehicle_time_s else
            direct[1] * defaults["direct_duration_multiplier"] + defaults["additive_buffer_min"] * 60,
            latest_arrival=trip.latest_arrival, max_price_vnd=view.quoted_price_cap_vnd, budget_max_vnd=trip.budget_max,
            walk_m=0, max_walk_m=trip.max_walk_m or 0, same_gender=trip.same_gender_coride,
            verified_gender=genders.get(view.user_id)))
    remaining = tuple(Stop(node, x.kind, str(x.booking_id)) for x, node in ahead)
    if not any(x.kind == DROPOFF for x, _ in ahead):
        return None
    return PlanState(rec.plan_id, rec.plan_version, _state(s), curr, now, rec.completed_stop_index + 1, remaining,
                     tuple(riders))
