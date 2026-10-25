"""Deterministic OSRM latency benchmark for the Phase 0 target (Revision 9 §79:
"OSRM returns a distance/duration matrix in < 50 ms").

Usage (repository root, stack running):
    python scripts/osrm_benchmark.py [--out FILE] [--iterations 50] [--seed 20261024]

Method:
  * Points are drawn uniformly from the Hanoi urban bbox with a fixed seed, so
    every run requests exactly the same coordinates, then snapped onto each
    profile's road network with /nearest (snap distances are reported).
  * A timed request counts as successful only if it returns HTTP 200,
    code "Ok" and a complete N x N durations + distances matrix (no nulls);
    otherwise it is counted as a failure and excluded from the percentiles.
  * For each profile (car, motorbike) and matrix size N in {10, 25, 50, 100}:
    /table N x N with annotations=duration,distance; 5 warm-up requests, then
    `iterations` timed requests (default: new connection per request, see --connection).
  * Also times /route Phenikaa -> Dong Da.
  * Latency is measured client-side on the host (includes HTTP + Docker port
    forwarding), so it is an upper bound on OSRM compute time.
"""

from __future__ import annotations

import argparse
import http.client
import json
import platform
import random
import socket
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
URBAN_BBOX = (105.70, 20.93, 105.92, 21.10)  # min_lon, min_lat, max_lon, max_lat
SIZES = (10, 25, 50, 100)
WARMUP = 5
TARGET_MS = 50.0


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = REPO_ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def pct(values: list[float], q: float) -> float:
    s = sorted(values)
    idx = min(len(s) - 1, max(0, round(q / 100 * len(s) + 0.5) - 1))
    return s[idx]


CONNECTION_MODE = "close"  # set from --connection
_keepalive: dict[tuple[str, int], http.client.HTTPConnection] = {}


def timed_get(addr: tuple[str, int], path: str) -> tuple[float, dict[str, Any] | None]:
    """Returns (latency_ms, body) or (latency_ms, None) when the response is not a valid Ok.

    "close": a new TCP connection per request with `Connection: close`; the time
    includes the TCP connect. "keepalive": one persistent connection per server
    (TCP_NODELAY). osrm-routed v5.27.1 answers small keep-alive requests ~40 ms
    late (delayed-ACK interaction), so "close" is the default.
    """
    start = time.perf_counter()
    if CONNECTION_MODE == "keepalive":
        conn = _keepalive.get(addr)
        if conn is None:
            conn = http.client.HTTPConnection(addr[0], addr[1], timeout=30)
            conn.connect()
            conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            _keepalive[addr] = conn
            start = time.perf_counter()
        conn.request("GET", path)
    else:
        conn = http.client.HTTPConnection(addr[0], addr[1], timeout=30)
        conn.request("GET", path, headers={"Connection": "close"})
    resp = conn.getresponse()
    body = resp.read()
    ms = (time.perf_counter() - start) * 1000
    if CONNECTION_MODE != "keepalive":
        data = json.loads(body)
    if resp.status != 200 or data.get("code") != "Ok":
        return ms, None
    return ms, data


def valid_table(data: dict[str, Any] | None, n: int) -> bool:
    """A complete n x n matrix with both annotations and no null cells."""
    if data is None:
        return False
    for key in ("durations", "distances"):
        m = data.get(key)
        if not m or len(m) != n or any(len(row) != n or None in row for row in m):
            return False
    return True


def snap_points(addr: tuple[str, int], raw: list[tuple[float, float]]) -> tuple[list[tuple[float, float]], list[float]]:
    """Snap each random point onto the profile's road network via /nearest."""
    snapped, dists = [], []
    for lon, lat in raw:
        _, data = timed_get(addr, f"/nearest/v1/driving/{lon:.6f},{lat:.6f}")
        if data is None:
            raise RuntimeError(f"/nearest failed for {lon},{lat}")
        wp = data["waypoints"][0]
        snapped.append(tuple(wp["location"]))
        dists.append(wp["distance"])
    return snapped, dists


def docker_stats() -> dict[str, str]:
    try:
        out = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}"],
            capture_output=True, text=True, timeout=30,
        ).stdout
        return {n: f"cpu={c} mem={m}" for n, c, m in (l.split("|") for l in out.splitlines() if l)}
    except Exception as exc:  # noqa: BLE001 - stats are informational
        return {"error": str(exc)}


def summarize(samples: list[float]) -> dict[str, float]:
    return {
        "p50_ms": round(pct(samples, 50), 2),
        "p95_ms": round(pct(samples, 95), 2),
        "p99_ms": round(pct(samples, 99), 2),
        "max_ms": round(max(samples), 2),
        "mean_ms": round(statistics.fmean(samples), 2),
    }


def bench_profile(addr: tuple[str, int], raw_points: list[tuple[float, float]], iterations: int) -> dict[str, Any]:
    points, snap = snap_points(addr, raw_points)
    out: dict[str, Any] = {
        "snap_distance_m": {"p50": round(pct(snap, 50), 1), "max": round(max(snap), 1)},
        "table": {},
    }
    for n in SIZES:
        coord = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in points[:n])
        path = f"/table/v1/driving/{coord}?annotations=duration,distance"
        for _ in range(WARMUP):
            timed_get(addr, path)
        samples, failures = [], 0
        for _ in range(iterations):
            ms, data = timed_get(addr, path)
            if valid_table(data, n):
                samples.append(ms)
            else:
                failures += 1
        entry: dict[str, Any] = {"points": n, "ok": len(samples), "failed": failures}
        if samples:
            entry.update(summarize(samples))
            entry["meets_target_p95"] = failures == 0 and pct(samples, 95) < TARGET_MS
        else:
            entry["meets_target_p95"] = False
        out["table"][f"{n}x{n}"] = entry
    out["docker_stats_after_tables"] = docker_stats()

    route = "/route/v1/driving/105.7477,20.9426;105.8270,21.0180?overview=false"
    for _ in range(WARMUP):
        timed_get(addr, route)
    samples, failures, last = [], 0, None
    for _ in range(iterations):
        ms, data = timed_get(addr, route)
        if data is None:
            failures += 1
        else:
            samples.append(ms)
            last = data
    out["route_phenikaa_dongda"] = {"ok": len(samples), "failed": failures,
                                    **(summarize(samples) if samples else {})}
    if last:
        out["route_phenikaa_dongda"].update(
            distance_km=round(last["routes"][0]["distance"] / 1000, 2),
            duration_min=round(last["routes"][0]["duration"] / 60, 1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261024)
    ap.add_argument("--iterations", type=int, default=50)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--connection", choices=("close", "keepalive"), default="close")
    ap.add_argument("--in-network", action="store_true",
                    help="run inside the compose network and call osrm-car:5000 / osrm-motorbike:5000 "
                         "directly (no Docker Desktop port forwarding)")
    args = ap.parse_args()
    global CONNECTION_MODE
    CONNECTION_MODE = args.connection

    env = load_env()
    rng = random.Random(args.seed)
    points = [(rng.uniform(URBAN_BBOX[0], URBAN_BBOX[2]), rng.uniform(URBAN_BBOX[1], URBAN_BBOX[3]))
              for _ in range(max(SIZES))]
    report: dict[str, Any] = {
        "run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "connection_mode": args.connection,
        "seed": args.seed, "iterations": args.iterations, "warmup": WARMUP,
        "bbox": URBAN_BBOX, "target_ms": TARGET_MS,
        "host": {"platform": platform.platform(), "processor": platform.processor()},
        "http": ("http.client inside the compose network, "
                 "client-side wall-clock latency") if args.in_network else
                ("http.client from the host to 127.0.0.1 "
                 "via Docker Desktop port forwarding, client-side wall-clock latency"),
        "docker_stats_before": docker_stats(),
        "profiles": {},
    }
    for profile, port_env, default in (("car", "OSRM_CAR_HOST_PORT", 5000),
                                       ("motorbike", "OSRM_MOTORBIKE_HOST_PORT", 5001)):
        addr = ((f"osrm-{profile}", 5000) if args.in_network
                else ("127.0.0.1", int(env.get(port_env, default))))
        report["profiles"][profile] = bench_profile(addr, points, args.iterations)

    for profile, res in report["profiles"].items():
        for size, s in res["table"].items():
            flag = "OK " if s["meets_target_p95"] else "MISS"
            if not s["ok"]:
                print(f"[{flag}] {profile:9s} table {size:7s} all {s['failed']} requests failed")
                continue
            print(f"[{flag}] {profile:9s} table {size:7s} ok={s['ok']} failed={s['failed']} "
                  f"p50={s['p50_ms']:7.2f} p95={s['p95_ms']:7.2f} mean={s['mean_ms']:7.2f} "
                  f"max={s['max_ms']:7.2f} ms")
        r = res["route_phenikaa_dongda"]
        print(f"       {profile:9s} route Phenikaa->Dong Da ok={r['ok']} p50={r['p50_ms']:.2f} "
              f"p95={r['p95_ms']:.2f} ms ({r.get('distance_km')} km, {r.get('duration_min')} min); "
              f"snap p50={res['snap_distance_m']['p50']} m max={res['snap_distance_m']['max']} m")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"report written to {args.out}")


if __name__ == "__main__":
    main()
