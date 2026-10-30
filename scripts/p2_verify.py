"""Independent checker of the P2 candidate generation (used by scripts/p2_benchmark.py).

Nothing here calls the generator, `pooling.insertion` or `candidate.constraints`: data is
read with its own SQL, roads come from OSRM directly (raw httpx), and the 11 hard
constraints of R9 Section 7 are re-derived:

  verify_candidate      a produced candidate: violations / borderline per HC
  check_single_reject   an evaluated driver without a candidate: was the rejection right?
  check_plan            an evaluated pool plan: the cheapest feasible insertion according to
                        tests/p2_reference.py (independent re-implementation + brute force)
                        on an independently fetched /table, compared with the generator

Table semantics (each leg independent, U-turn at a stop allowed) are what R9 Sections 34 /
36 specify; `legs(..., continue_straight=None)` gives the OSRM default for SF-P2-15.
"""

import itertools
import uuid
from datetime import datetime, timedelta

import httpx
from sqlalchemy import text

TOL_S, TOL_M = 1.0, 1.0  # per leg: OSRM /route vs /table rounding
DWELL_S, K_MAX, STALE_S = 60.0, 8, 120.0
WINDOW_MIN = {"BIKE_URBAN": (3, 15), "CAR_URBAN_PRIVATE": (5, 20), "CAR_URBAN_POOL": (5, 20)}
VEHICLE = {"BIKE_URBAN": "BIKE", "CAR_URBAN_PRIVATE": "CAR4", "CAR_URBAN_POOL": "CAR4"}


class Osrm:
    def __init__(self, urls: dict[str, str]) -> None:
        self.urls = urls
        self._memo: dict[tuple, object] = {}

    def legs(self, profile: str, pts: list[tuple[float, float]],
             continue_straight: str | None = "false") -> list[tuple[float, float]] | None:
        key = ("route", profile, tuple(pts), continue_straight)
        if key not in self._memo:
            params = {"overview": "false", "steps": "false", "exclude": "ferry"}
            if continue_straight is not None:
                params["continue_straight"] = continue_straight
            path = ";".join(f"{x:.6f},{y:.6f}" for x, y in pts)
            body = httpx.get(f"{self.urls[profile]}/route/v1/driving/{path}", params=params,
                             headers={"Connection": "close"}, timeout=15).json()
            self._memo[key] = (None if body.get("code") != "Ok"
                               else [(leg["distance"], leg["duration"]) for leg in body["routes"][0]["legs"]])
        return self._memo[key]  # type: ignore[return-value]

    def table(self, profile: str, pts: list[tuple[float, float]]) -> tuple[list, list]:
        path = ";".join(f"{x:.6f},{y:.6f}" for x, y in pts)
        body = httpx.get(f"{self.urls[profile]}/table/v1/driving/{path}",
                         params={"annotations": "distance,duration", "exclude": "ferry"},
                         headers={"Connection": "close"}, timeout=15).json()
        return body["distances"], body["durations"]


def fare(base: int, per_km: int, per_min: int, m: float, s: float) -> int:
    return int(round(base + per_km * m / 1000 + per_min * s / 60, 6) // 1000) * 1000


def max_price(service: str, direct: tuple[float, float]) -> int:
    if service == "BIKE_URBAN":
        return fare(10000, 4500, 250, *direct)
    private = fare(20000, 11000, 500, *direct)
    if service == "CAR_URBAN_PRIVATE":
        return private
    quote = int(round(private * 0.8, 6) // 1000) * 1000
    return int(round(quote + 0.5 * (private - quote), 6) // 1000) * 1000


def driver_row(session, driver_id: uuid.UUID, now: datetime) -> dict:  # noqa: ANN001
    return dict(session.execute(text(
        "SELECT dl.availability, ST_X(dl.geom) x, ST_Y(dl.geom) y, EXTRACT(EPOCH FROM (:now - dl.updated_at)) age, "
        "dp.kyc_status, dp.accepts_urban, dp.pool_enabled, dp.max_additional_pickups, dp.max_driver_detour_km, "
        "dp.max_driver_detour_min, v.vehicle_type, v.capacity, v.is_active, v.id vehicle_id FROM driver_locations dl "
        "JOIN driver_profiles dp ON dp.user_id = dl.driver_id LEFT JOIN vehicles v ON v.id = dl.active_vehicle_id "
        "WHERE dl.driver_id = :d"), {"d": driver_id, "now": now}).mappings().one())


def hc01_ok(d: dict, service: str, new_vehicle: bool) -> bool:
    return not (d["availability"] == "OFFLINE" or d["age"] > STALE_S or (new_vehicle and d["availability"] != "IDLE")
                or not d["is_active"] or d["vehicle_type"] != VEHICLE[service] or not d["accepts_urban"]
                or (service == "CAR_URBAN_POOL" and (not d["pool_enabled"] or d["kyc_status"] != "VERIFIED")))


def new_trip(session, trip_id: uuid.UUID) -> dict:  # noqa: ANN001
    r = dict(session.execute(text(
        "SELECT t.user_id, ST_X(t.pickup_geom) px, ST_Y(t.pickup_geom) py, ST_X(t.dropoff_geom) qx, "
        "ST_Y(t.dropoff_geom) qy, t.preferred_departure, t.created_at, t.budget_max, t.passenger_count, "
        "t.allowed_service_codes, COALESCE((t.categorical_preferences_json->>'same_gender_coride')::boolean, false) sg, "
        "CASE WHEN u.gender_verification_status = 'VERIFIED' THEN u.gender END vg "
        "FROM trip_requests t JOIN users u ON u.id = t.user_id WHERE t.id = :t"), {"t": trip_id}).mappings().one())
    r["p"], r["q"] = (r["px"], r["py"]), (r["qx"], r["qy"])
    return r


def plan_rows(session, plan_id: uuid.UUID) -> list[dict]:  # noqa: ANN001
    return [dict(x) for x in session.execute(text(
        "SELECT s.seq, s.booking_id, s.kind, s.status, s.completed_at, ST_X(s.geom) x, ST_Y(s.geom) y, b.seat_count, "
        "b.quoted_price_cap_vnd, p.traveled_km_before_last_replan km, p.direct_distance_m dm, p.direct_duration_s ds, "
        "t.preferred_departure, t.budget_max, "
        "COALESCE((t.categorical_preferences_json->>'same_gender_coride')::boolean, false) sg, "
        "CASE WHEN u.gender_verification_status = 'VERIFIED' THEN u.gender END vg "
        "FROM ride_stops s JOIN bookings b ON b.id = s.booking_id JOIN ride_participants p ON p.booking_id = s.booking_id "
        "JOIN trip_requests t ON t.id = b.request_id JOIN users u ON u.id = b.user_id "
        "WHERE s.ride_plan_id = :p ORDER BY s.seq"), {"p": plan_id}).mappings().all()]


def old_riders(rows: list[dict]) -> dict[str, dict]:
    riders: dict[str, dict] = {}
    for r in rows:
        ref = str(r["booking_id"])
        x = riders.setdefault(ref, {"onboard": False})
        if r["status"] == "COMPLETED" and r["kind"] == "PICKUP":
            x |= {"onboard": True, "boarded": r["completed_at"]}
        x |= {"seats": r["seat_count"], "direct": (r["dm"], r["ds"]), "traveled": r["km"] * 1000,
              "max_price": r["quoted_price_cap_vnd"], "budget": r["budget_max"], "same_gender": r["sg"],
              "gender": r["vg"], "window": (r["preferred_departure"] + timedelta(minutes=5),
                                            r["preferred_departure"] + timedelta(minutes=20))}
        if r["status"] == "PLANNED":
            x[r["kind"]] = (r["x"], r["y"])
    return {k: v for k, v in riders.items() if "DROPOFF" in v}  # finished riders are out of the plan


def walk(chain: list[tuple[str, str]], legs: list[tuple[float, float]], riders: dict, now: datetime):  # noqa: ANN201
    """Times (s after now) and distance at each stop: dwell 60 s, wait for T_earliest at pickups."""
    clock = dist = 0.0
    at, loads, aboard = {}, [], {k for k, r in riders.items() if r["onboard"]}
    seats = sum(r["seats"] for r in riders.values() if r["onboard"])
    pairs = set(itertools.combinations(sorted(aboard), 2))
    for (ref, kind), (lm, ls) in zip(chain, legs, strict=True):
        loads.append(seats)
        clock += ls
        dist += lm
        r = riders[ref]
        if kind == "PICKUP":
            clock = max(clock, (r["window"][0] - now).total_seconds())
            seats += r["seats"]
            pairs |= {tuple(sorted((o, ref))) for o in aboard}
            aboard.add(ref)
        else:
            seats -= r["seats"]
            aboard.discard(ref)
        at[(ref, kind)] = (clock, dist)
        clock += DWELL_S
    return at, loads, pairs, dist, clock


def verify_candidate(c, session, osrm: Osrm, trip_id: uuid.UUID, now: datetime,  # noqa: ANN001
                     continue_straight: str | None = "false") -> tuple[set[str], set[str]]:
    """continue_straight="false": table semantics (R9). None: OSRM default (no U-turn at a stop
    for the car profile) - used only to measure SF-P2-15."""
    bad, edge = set(), set()
    service, profile = c.service_code, ("motorbike" if c.service_code == "BIKE_URBAN" else "car")
    t = new_trip(session, trip_id)
    d = driver_row(session, c.driver_id, now)
    if not hc01_ok(d, service, c.source_type == "NEW_SINGLE_VEHICLE"):
        bad.add("HC01")
    lead = t["preferred_departure"] - t["created_at"]
    if service not in t["allowed_service_codes"] or not timedelta(0) <= lead <= timedelta(hours=12):
        bad.add("HC09")
    direct = osrm.legs(profile, [t["p"], t["q"]])
    if direct is None:
        return bad | {"HC02"}, edge
    lo, hi = WINDOW_MIN[service]
    riders = {"new": {"onboard": False, "seats": t["passenger_count"], "direct": direct[0], "traveled": 0.0,
                      "max_price": max_price(service, direct[0]), "budget": t["budget_max"], "same_gender": t["sg"],
                      "gender": t["vg"], "PICKUP": t["p"], "DROPOFF": t["q"],
                      "window": (t["preferred_departure"] + timedelta(minutes=lo),
                                 t["preferred_departure"] + timedelta(minutes=hi))}}
    completed = 0
    old_chain: list[tuple[str, str]] = []
    if c.plan_id:
        rows = plan_rows(session, c.plan_id)
        completed = sum(r["status"] == "COMPLETED" for r in rows)
        riders |= old_riders(rows)
        old_chain = [(str(r["booking_id"]), r["kind"]) for r in rows if r["status"] == "PLANNED"]
        if completed + len(c.insertion["chain"]) > K_MAX or len(riders) - 1 > d["max_additional_pickups"]:
            bad.add("HC07")
    chain = [tuple(x) for x in c.insertion["chain"]]
    pos = (d["x"], d["y"])
    legs = osrm.legs(profile, [pos] + [riders[r][k] for r, k in chain], continue_straight)
    if legs is None:
        return bad | {"HC02"}, edge
    at, loads, pairs, dist, clock = walk(chain, legs, riders, now)
    n = len(legs)
    if any(x > d["capacity"] for x in loads):
        bad.add("HC04")
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
        dm, ds = r["direct"]
        if inveh > ds * 1.5 + 600 + TOL_S * n:
            bad.add("HC06")
        elif inveh > ds * 1.5 + 600:
            edge.add("HC06")
        if service == "CAR_URBAN_POOL" and dm:
            if ride > 1.3 * dm + TOL_M * n:
                bad.add("HC05")
            elif ride > 1.3 * dm:
                edge.add("HC05")
        if r["budget"] is not None and r["max_price"] > r["budget"]:
            bad.add("HC08")
        # HC10: P2 has no meeting points (C9): walk is 0 by construction, nothing to violate.
    for a, b in pairs:
        ra, rb = riders[a], riders[b]
        if (ra["same_gender"] or rb["same_gender"]) and (ra["gender"] is None or ra["gender"] != rb["gender"]):
            bad.add("HC11")
    if c.plan_id and (d["max_driver_detour_km"] is not None or d["max_driver_detour_min"] is not None):
        old_legs = osrm.legs("car", [pos] + [riders[r][k] for r, k in old_chain], continue_straight) if old_chain else []
        _, _, _, old_dist, old_clock = walk(old_chain, old_legs, riders, now) if old_chain else (0, 0, 0, 0.0, 0.0)
        tol = n + len(old_legs)
        for added, limit, scale in ((dist - old_dist, d["max_driver_detour_km"], 1000),
                                    (clock - old_clock, d["max_driver_detour_min"], 60)):
            if limit is None:
                continue
            if added > limit * scale + tol:
                bad.add("HC07")
            elif added > limit * scale:
                edge.add("HC07")
    return bad, edge


def check_single_reject(session, osrm: Osrm, service: str, driver_id: uuid.UUID, trip_id: uuid.UUID,  # noqa: ANN001
                        now: datetime) -> str:
    """'correct' if R9 Section 7 independently rejects this driver too, else 'missed'."""
    t = new_trip(session, trip_id)
    d = driver_row(session, driver_id, now)
    profile = "motorbike" if service == "BIKE_URBAN" else "car"
    if not hc01_ok(d, service, True):
        return "correct"
    legs = osrm.legs(profile, [(d["x"], d["y"]), t["p"], t["q"]])
    if legs is None or t["passenger_count"] > d["capacity"]:
        return "correct"
    lo, hi = WINDOW_MIN[service]
    pick = max(legs[0][1], (t["preferred_departure"] + timedelta(minutes=lo) - now).total_seconds())
    latest = (t["preferred_departure"] + timedelta(minutes=hi) - now).total_seconds()
    if pick > latest:
        return "correct"
    if t["budget_max"] is not None and max_price(service, legs[1]) > t["budget_max"]:
        return "correct"
    # in-vehicle = direct; no co-rider -> HC05/06/07/10/11 cannot fail for a single vehicle
    return "borderline" if pick > latest - 2 * TOL_S else "missed"


def check_plan(session, osrm: Osrm, plan_id: uuid.UUID, trip_id: uuid.UUID, now: datetime,  # noqa: ANN001
               produced_delta_vnd: float | None) -> str:
    """Brute force of tests/p2_reference.py on an independent table: 'correct' when both agree
    that no insertion exists, 'optimal' when both find one with the same cost, otherwise
    'missed' (reference feasible, generator none), 'extra' (generator only) or 'cost_mismatch'."""
    from app.modules.candidate.constraints import DriverState  # data container only
    from app.modules.pooling.insertion import PlanState, RiderSpec, Stop  # data containers only
    import p2_reference as ref

    t = new_trip(session, trip_id)
    rows = plan_rows(session, plan_id)
    head = session.execute(text("SELECT driver_id FROM ride_plans WHERE id = :p"), {"p": plan_id}).scalar_one()
    d = driver_row(session, head, now)
    riders = old_riders(rows)
    ahead = [(str(r["booking_id"]), r["kind"]) for r in rows if r["status"] == "PLANNED"]
    pts = [(d["x"], d["y"])] + [riders[r][k] for r, k in ahead] + [t["p"], t["q"]]
    D, T = osrm.table("car", pts)
    p_node, q_node = len(pts) - 2, len(pts) - 1

    def spec(refname: str, r: dict) -> RiderSpec:
        return RiderSpec(ref=refname, seats=r["seats"], onboard=r["onboard"],
                         pickup_window=None if r["onboard"] else r["window"], actual_pickup=r.get("boarded"),
                         traveled_m=r["traveled"], direct_distance_m=r["direct"][0], direct_duration_s=r["direct"][1],
                         max_detour_ratio=0.30, max_in_vehicle_s=r["direct"][1] * 1.5 + 600, latest_arrival=None,
                         max_price_vnd=r["max_price"], budget_max_vnd=r["budget"], same_gender=r["same_gender"],
                         verified_gender=r["gender"])

    direct = (D[p_node][q_node], T[p_node][q_node])
    new = {"onboard": False, "seats": t["passenger_count"], "direct": direct, "traveled": 0.0,
           "max_price": max_price("CAR_URBAN_POOL", direct), "budget": t["budget_max"], "same_gender": t["sg"],
           "gender": t["vg"], "window": (t["preferred_departure"] + timedelta(minutes=5),
                                         t["preferred_departure"] + timedelta(minutes=20))}
    state = PlanState(plan_id, None, DriverState(
        driver_id=head, availability=d["availability"], location_age_s=float(d["age"]), kyc_status=d["kyc_status"],
        accepts_urban=d["accepts_urban"], pool_enabled=d["pool_enabled"], accepts_intercity=False,
        max_additional_pickups=d["max_additional_pickups"], max_driver_detour_km=d["max_driver_detour_km"],
        max_driver_detour_min=d["max_driver_detour_min"], vehicle_id=d["vehicle_id"], vehicle_type=d["vehicle_type"],
        capacity=d["capacity"], vehicle_active=d["is_active"]), 0, now,
        sum(r["status"] == "COMPLETED" for r in rows),
        tuple(Stop(i + 1, k, r) for i, (r, k) in enumerate(ahead)), tuple(spec(k, v) for k, v in riders.items()))
    best = ref.brute_force(state, spec("new", new), p_node, q_node, D, T, "CAR_URBAN_POOL", "EXISTING_POOL_PLAN",
                           DWELL_S, K_MAX, STALE_S, 11000, 500)
    if best is None:
        return "correct" if produced_delta_vnd is None else "extra"
    if produced_delta_vnd is None:
        return "missed"
    return "optimal" if abs(produced_delta_vnd - 2 * 5000 - best) < 1.0 else "cost_mismatch"
