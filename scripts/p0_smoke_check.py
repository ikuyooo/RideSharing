"""Phase 0 acceptance smoke checks (re-runnable, stdlib only).

Usage (from the repository root, with the stack running):
    python scripts/p0_smoke_check.py                 # service checks
    python scripts/p0_smoke_check.py --restart-test  # + persistence across restarts
    python scripts/p0_smoke_check.py --json-out FILE # also write results as JSON

Postgres and Redis are probed through `docker compose exec` so no host
database clients are required. Exit code is non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]

# Reference points (lon, lat) from Revision 9 examples.
PHENIKAA = (105.7477, 20.9426)       # Dai hoc Phenikaa, Ha Dong
DONG_DA = (105.8270, 21.0180)        # Dong Da
LA_PHU = (105.7340, 20.9690)         # La Phu, Hoai Duc
HOAN_KIEM = (105.8542, 21.0285)
NINH_BINH = (105.9745, 20.2506)      # reached by car via the CT01 expressway
HAI_PHONG = (106.6822, 20.8449)
HA_DONG = (105.7759, 20.9714)
HUNG_YEN = (106.0510, 20.6460)       # TP Hung Yen, intercity example in Section 28.2
THAI_NGUYEN = (105.8442, 21.5928)
VINH_OUTSIDE = (105.6813, 18.6796)   # Vinh, outside the clipped extract

# Inside the bbox (104.30,19.60,107.50,22.50) but close to its edges.
BOUNDARY_POINTS = {
    "Thanh Hoa (S)": (105.7760, 19.8070),
    "Ha Long (E)": (107.0843, 20.9510),
    "Tuyen Quang (W)": (105.2180, 21.8230),
    "Lang Son (NE)": (106.7570, 21.8530),
}

MOTORWAY_TEST_PAIRS = {
    "Hoan Kiem->Ninh Binh": (HOAN_KIEM, NINH_BINH),
    "Hoan Kiem->Hai Phong": (HOAN_KIEM, HAI_PHONG),
    "Ha Dong->TP Hung Yen": (HA_DONG, HUNG_YEN),
    "Hoan Kiem->Thai Nguyen": (HOAN_KIEM, THAI_NGUYEN),
}

results: list[dict[str, Any]] = []


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = REPO_ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()


def port(name: str, default: int) -> int:
    return int(ENV.get(name, default))


def check(name: str) -> Callable[[Callable[[], str]], Callable[[], None]]:
    def deco(fn: Callable[[], str]) -> Callable[[], None]:
        def run() -> None:
            start = time.perf_counter()
            try:
                detail, ok = fn(), True
            except Exception as exc:  # noqa: BLE001
                detail, ok = f"{type(exc).__name__}: {exc}", False
            ms = round((time.perf_counter() - start) * 1000, 1)
            results.append({"check": name, "ok": ok, "ms": ms, "detail": detail})
            print(f"[{'PASS' if ok else 'FAIL'}] {name} ({ms} ms) - {detail}")

        return run

    return deco


def compose(*args: str, input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["docker", "compose", *args],
        cwd=REPO_ROOT, input=input_text, capture_output=True, timeout=180,
        encoding="utf-8", errors="replace",  # OSM names are UTF-8; Windows default is cp1252
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def psql(sql: str) -> str:
    user = ENV.get("POSTGRES_USER", "ridesharing")
    db = ENV.get("POSTGRES_DB", "ridesharing")
    return compose("exec", "-T", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-qtA",
                   "-U", user, "-d", db, input_text=sql)


def redis_cli(*args: str) -> str:
    return compose("exec", "-T", "redis", "sh", "-c",
                   'redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ' + " ".join(args))


def http_json(url: str) -> tuple[int, dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


def coords(*pts: tuple[float, float]) -> str:
    return ";".join(f"{lon},{lat}" for lon, lat in pts)


# --- checks -------------------------------------------------------------------

@check("compose: all default services healthy")
def c_compose() -> str:
    out = compose("ps", "--format", "{{.Service}}={{.Health}}")
    states = dict(line.split("=", 1) for line in out.splitlines() if line)
    expected = {"postgres", "redis", "osrm-car", "osrm-motorbike", "backend"}
    bad = {s: states.get(s, "missing") for s in expected if states.get(s) != "healthy"}
    if bad:
        raise RuntimeError(f"not healthy: {bad}")
    return ", ".join(f"{s}={states[s]}" for s in sorted(expected))


@check("postgres: version + PostGIS extension")
def c_pg_version() -> str:
    out = psql("SELECT current_setting('server_version'), extversion "
               "FROM pg_extension WHERE extname = 'postgis';")
    pg, postgis = out.split("|")
    if not pg.startswith("16.") or not postgis.startswith("3.4"):
        raise RuntimeError(f"unexpected versions pg={pg} postgis={postgis}")
    return f"PostgreSQL {pg}, PostGIS {postgis}"


@check("postgres: spatial query with GIST index")
def c_pg_spatial() -> str:
    out = psql(f"""
        CREATE TEMP TABLE p0_points (name text, geom geometry(Point, 4326));
        CREATE INDEX ON p0_points USING GIST (geom);
        INSERT INTO p0_points VALUES
          ('phenikaa', ST_SetSRID(ST_MakePoint({PHENIKAA[0]}, {PHENIKAA[1]}), 4326)),
          ('la_phu',   ST_SetSRID(ST_MakePoint({LA_PHU[0]}, {LA_PHU[1]}), 4326)),
          ('hoan_kiem',ST_SetSRID(ST_MakePoint({HOAN_KIEM[0]}, {HOAN_KIEM[1]}), 4326));
        SELECT string_agg(name, ',' ORDER BY name)
          FROM p0_points
         WHERE ST_DWithin(geom::geography,
                          ST_SetSRID(ST_MakePoint({PHENIKAA[0]}, {PHENIKAA[1]}), 4326)::geography,
                          5000);
        SELECT round(ST_Distance(
                 ST_SetSRID(ST_MakePoint({PHENIKAA[0]}, {PHENIKAA[1]}), 4326)::geography,
                 ST_SetSRID(ST_MakePoint({HOAN_KIEM[0]}, {HOAN_KIEM[1]}), 4326)::geography));
    """)
    within, dist_m = out.splitlines()[-2:]
    if within != "la_phu,phenikaa":
        raise RuntimeError(f"ST_DWithin returned {within!r}")
    if not 12000 < float(dist_m) < 16000:
        raise RuntimeError(f"implausible distance {dist_m} m")
    return f"ST_DWithin(5 km of Phenikaa)={within}; geodesic Phenikaa-Hoan Kiem={dist_m} m"


@check("redis: PING + SET/GET with TTL")
def c_redis() -> str:
    if redis_cli("PING") != "PONG":
        raise RuntimeError("PING failed")
    redis_cli("SET", "p0:smoke", "ok", "EX", "60")
    val, ttl = redis_cli("GET", "p0:smoke"), int(redis_cli("TTL", "p0:smoke"))
    if val != "ok" or not 0 < ttl <= 60:
        raise RuntimeError(f"GET={val!r} TTL={ttl}")
    return f"PONG; GET=ok TTL={ttl}s; version {redis_cli('INFO', 'server').split('redis_version:')[1].split()[0]}"


def osrm_checks(profile: str, port_env: str, default_port: int) -> None:
    base = f"http://127.0.0.1:{port(port_env, default_port)}"

    @check(f"osrm-{profile}: nearest at Hoan Kiem snaps onto the road network")
    def c_nearest() -> str:
        code, body = http_json(f"{base}/nearest/v1/driving/{coords(HOAN_KIEM)}?number=1")
        if code != 200 or body.get("code") != "Ok" or not body.get("waypoints"):
            raise RuntimeError(f"HTTP {code} {body.get('code')}")
        wp = body["waypoints"][0]
        lon, lat = wp["location"]
        if wp["distance"] > 100 or not (105.8 < lon < 105.9 and 21.0 < lat < 21.06):
            raise RuntimeError(f"bad snap {wp}")
        return f"snapped {wp['distance']:.1f} m to '{wp.get('name', '')}' at ({lon:.5f},{lat:.5f})"

    @check(f"osrm-{profile}: route Phenikaa -> Dong Da (distance, duration, geometry)")
    def c_route() -> str:
        code, body = http_json(f"{base}/route/v1/driving/{coords(PHENIKAA, DONG_DA)}"
                               "?overview=full&geometries=geojson")
        if code != 200 or body.get("code") != "Ok":
            raise RuntimeError(f"HTTP {code} {body.get('code')}")
        r = body["routes"][0]
        line = r["geometry"]["coordinates"]
        if not 5000 < r["distance"] < 30000 or r["duration"] <= 0:
            raise RuntimeError(f"implausible distance/duration {r['distance']} m {r['duration']} s")
        if r["geometry"]["type"] != "LineString" or len(line) < 2:
            raise RuntimeError("missing geometry")
        if any(not (104.3 <= x <= 107.5 and 19.6 <= y <= 22.5) for x, y in line):
            raise RuntimeError("geometry leaves the extract bbox")
        return (f"{r['distance'] / 1000:.2f} km, {r['duration'] / 60:.1f} min, "
                f"geometry {len(line)} pts, avg {r['distance'] / r['duration'] * 3.6:.1f} km/h")

    @check(f"osrm-{profile}: table 3x3 (shape, diagonal, units)")
    def c_table() -> str:
        code, body = http_json(f"{base}/table/v1/driving/{coords(PHENIKAA, LA_PHU, DONG_DA)}"
                               "?annotations=duration,distance")
        if code != 200 or body.get("code") != "Ok":
            raise RuntimeError(f"HTTP {code} {body.get('code')}")
        dur, dist = body["durations"], body["distances"]
        if len(dur) != 3 or any(len(row) != 3 for row in dur + dist):
            raise RuntimeError("matrix shape is not 3x3")
        for i in range(3):
            for j in range(3):
                if dur[i][j] is None or dist[i][j] is None:
                    raise RuntimeError(f"null cell ({i},{j})")
                if i == j and (dur[i][j] != 0 or dist[i][j] != 0):
                    raise RuntimeError(f"non-zero diagonal ({i},{i})")
                if i != j:
                    kmh = dist[i][j] / dur[i][j] * 3.6  # metres / seconds -> km/h
                    if not 5 <= kmh <= 120:
                        raise RuntimeError(f"implausible speed {kmh:.1f} km/h at ({i},{j})")
        return (f"row0 distance(m)={[round(x) for x in dist[0]]} "
                f"duration(s)={[round(x) for x in dur[0]]}")

    @check(f"osrm-{profile}: routes to points near the extract boundary")
    def c_boundary() -> str:
        out = []
        for name, pt in BOUNDARY_POINTS.items():
            code, body = http_json(f"{base}/route/v1/driving/{coords(HOAN_KIEM, pt)}?overview=false")
            if code != 200 or body.get("code") != "Ok":
                raise RuntimeError(f"{name}: HTTP {code} {body.get('code')}")
            snap = body["waypoints"][1]["distance"]
            r = body["routes"][0]
            if snap > 200 or r["distance"] <= 0 or r["duration"] <= 0:
                raise RuntimeError(f"{name}: snap={snap:.0f} m distance={r['distance']}")
            out.append(f"{name} {r['distance'] / 1000:.1f} km/{r['duration'] / 60:.0f} min")
        return "; ".join(out)

    @check(f"osrm-{profile}: error and out-of-coverage handling")
    def c_errors() -> str:
        code, body = http_json(f"{base}/route/v1/driving/200,95;105.85,21.03")
        if code != 400 or body.get("code") not in ("InvalidValue", "InvalidQuery", "InvalidUrl"):
            raise RuntimeError(f"invalid coordinate gave HTTP {code} {body.get('code')}")
        _, near = http_json(f"{base}/nearest/v1/driving/{coords(VINH_OUTSIDE)}")
        snap_km = near["waypoints"][0]["distance"] / 1000
        if snap_km < 50:
            raise RuntimeError(f"point outside the extract snapped only {snap_km:.1f} km away")
        return (f"invalid coordinate -> HTTP 400 {body['code']}; point outside extract (Vinh) "
                f"snaps {snap_km:.0f} km away -> callers must reject large snap distances")

    c_nearest()
    c_route()
    c_table()
    c_boundary()
    c_errors()


def restricted_edges() -> dict[str, set[frozenset[int]]]:
    """Undirected node-pair edges of OSM ways a motorbike must not use, read
    from the same region.osm.pbf the graphs were built from (via osmium)."""
    script = (
        "osmium tags-filter -R -O -o /tmp/mw.osm.pbf /data/region.osm.pbf "
        "w/highway=motorway,motorway_link && osmium cat -f opl /tmp/mw.osm.pbf && "
        "echo '#SPLIT' && "
        "osmium tags-filter -R -O -o /tmp/mc.osm.pbf /data/region.osm.pbf w/motorcycle=no && "
        "osmium cat -f opl /tmp/mc.osm.pbf"
    )
    out = compose("--profile", "osrm-prep", "run", "--rm", "--no-deps", "-T",
                  "--entrypoint", "sh", "osm-fetch", "-c", script)
    sets: dict[str, set[frozenset[int]]] = {"motorway": set(), "motorcycle=no": set()}
    current = "motorway"
    for line in out.splitlines():
        if line == "#SPLIT":
            current = "motorcycle=no"
            continue
        if not line.startswith("w"):
            continue
        nodes_field = next((f for f in line.split(" ") if f.startswith("N")), "N")
        nodes = [int(n[1:]) for n in nodes_field[1:].split(",") if n]
        sets[current].update(frozenset(p) for p in zip(nodes, nodes[1:]) if p[0] != p[1])
    return sets


def route_edges(profile_port: int, a: tuple[float, float], b: tuple[float, float]) -> list[frozenset[int]]:
    code, body = http_json(f"http://127.0.0.1:{profile_port}/route/v1/driving/"
                           f"{coords(a, b)}?overview=false&annotations=nodes")
    if code != 200 or body.get("code") != "Ok":
        raise RuntimeError(f"HTTP {code} {body.get('code')}")
    edges: list[frozenset[int]] = []
    for leg in body["routes"][0]["legs"]:
        nodes = leg["annotation"]["nodes"]
        edges.extend(frozenset(p) for p in zip(nodes, nodes[1:]) if p[0] != p[1])
    return edges


@check("osrm profiles: motorbike uses no motorway / motorcycle=no OSM edge (car does)")
def c_motorway() -> str:
    restricted = restricted_edges()
    mw, mc = restricted["motorway"], restricted["motorcycle=no"]
    if not mw:
        raise RuntimeError("no motorway edges found in the extract")
    car_port = port("OSRM_CAR_HOST_PORT", 5000)
    bike_port = port("OSRM_MOTORBIKE_HOST_PORT", 5001)
    car_hits = 0
    rows = []
    for name, (a, b) in MOTORWAY_TEST_PAIRS.items():
        car = route_edges(car_port, a, b)
        bike = route_edges(bike_port, a, b)
        c_mw = sum(e in mw for e in car)
        b_mw = sum(e in mw for e in bike)
        b_mc = sum(e in mc for e in bike)
        car_hits += c_mw
        if b_mw or b_mc:
            raise RuntimeError(f"{name}: motorbike route has {b_mw} motorway and {b_mc} motorcycle=no edges")
        rows.append(f"{name}: car {c_mw}/{len(car)} motorway edges, motorbike 0/{len(bike)}")
    if car_hits == 0:
        raise RuntimeError("car used no motorway edge; test pairs are not discriminating")
    return (f"OSM restricted edges: motorway={len(mw)}, motorcycle=no={len(mc)}. " + "; ".join(rows))


@check("backend: /health/live")
def c_live() -> str:
    code, body = http_json(f"http://127.0.0.1:{port('BACKEND_HOST_PORT', 8000)}/health/live")
    if code != 200 or body.get("status") != "ok":
        raise RuntimeError(f"HTTP {code} {body}")
    return "ok"


@check("backend: /health/ready (all dependencies)")
def c_ready() -> str:
    code, body = http_json(f"http://127.0.0.1:{port('BACKEND_HOST_PORT', 8000)}/health/ready")
    if code != 200 or body.get("status") != "ok":
        raise RuntimeError(f"HTTP {code} {json.dumps(body.get('checks'))}")
    return (f"{body['config_baseline_version']} / {body['pricing_version']}; "
            + ", ".join(f"{k}={v['status']}" for k, v in body["checks"].items()))


def osrm_stamp(service: str) -> str:
    return compose("exec", "-T", service, "cat", "/data/PREPARED.key")


@check("persistence: full stack restart keeps postgres/redis data and OSRM graphs")
def c_restart() -> str:
    services = ["postgres", "redis", "osrm-car", "osrm-motorbike", "backend"]
    marker = f"p0-{int(time.time())}"
    psql("CREATE TABLE IF NOT EXISTS p0_persistence_probe (marker text PRIMARY KEY, created_at timestamptz DEFAULT now());"
         f"INSERT INTO p0_persistence_probe (marker) VALUES ('{marker}');")
    redis_cli("SET", "p0:persist", marker)
    stamps = {s: osrm_stamp(s) for s in ("osrm-car", "osrm-motorbike")}

    start = time.perf_counter()
    compose("restart", *services)  # restart only; volumes are never removed
    for _ in range(120):
        out = compose("ps", "--format", "{{.Service}}={{.Health}}", *services)
        if out.count("=healthy") == len(services):
            break
        time.sleep(2)
    else:
        raise RuntimeError(f"services not healthy after restart: {out}")
    ready_s = time.perf_counter() - start

    pg_ok = psql(f"SELECT count(*) FROM p0_persistence_probe WHERE marker = '{marker}';") == "1"
    rd_ok = redis_cli("GET", "p0:persist") == marker
    stamps_ok = all(osrm_stamp(s) == v for s, v in stamps.items())
    code, body = http_json(f"http://127.0.0.1:{port('OSRM_MOTORBIKE_HOST_PORT', 5001)}"
                           f"/route/v1/driving/{coords(PHENIKAA, DONG_DA)}?overview=false")
    route_ok = code == 200 and body.get("code") == "Ok"
    psql("DROP TABLE p0_persistence_probe;")
    redis_cli("DEL", "p0:persist")
    if not (pg_ok and rd_ok and stamps_ok and route_ok):
        raise RuntimeError(f"postgres={pg_ok} redis={rd_ok} osrm_stamps={stamps_ok} route={route_ok}")
    return (f"all {len(services)} services healthy {ready_s:.0f}s after restart; marker {marker} found in "
            "postgres and redis (AOF); OSRM build stamps unchanged and routing answers without "
            "re-preprocessing (probe cleaned up)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--restart-test", action="store_true")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    c_compose()
    c_pg_version()
    c_pg_spatial()
    c_redis()
    osrm_checks("car", "OSRM_CAR_HOST_PORT", 5000)
    osrm_checks("motorbike", "OSRM_MOTORBIKE_HOST_PORT", 5001)
    c_motorway()
    c_live()
    c_ready()
    if args.restart_test:
        c_restart()

    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps({
            "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": results,
        }, indent=2), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
