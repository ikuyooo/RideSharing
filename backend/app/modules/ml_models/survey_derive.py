"""Survey S1 - sourced ETA for the 6 km context (owner decision "PHASE 1 FINAL
CLOSURE", survey item 1: prices from the locked formulas + an ETA with a source).

Revision 9 (preamble) states that in simulations / experiments "quãng đường và thời
gian di chuyển được lấy trực tiếp từ OSRM". This module measures OSRM car and
motorbike road distance and duration between seeded pairs of OSM place nodes
inside the URBAN polygon of one service-area version, and reports the medians for
pairs of ~6 km - plus the same statistic for ~14 km pairs as a control against
the 14 km values Revision 9 publishes (Section 10.4: car 40 min, motorbike 35 min).

Read-only; prints JSON. Nothing is written to pricing_configs (research
parameters stay in the survey files).

Run (compose): docker compose --profile service-area run --rm service-area-build \
    python -m app.modules.ml_models.survey_derive --version <service_area_version>
"""

import argparse
import json
import random
import statistics
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import create_engine, text

from app.core.settings import get_settings

PLACE_KINDS = ("suburb", "quarter", "neighbourhood", "village", "hamlet", "town")
N_POINTS = 150          # one OSRM /table request per profile (server max-table-size 200)
SEED = 1
BANDS_KM = {"6": (5.5, 6.5), "14": (13.5, 14.5)}
R9_14KM_MIN = {"car": 40, "motorbike": 35}  # Revision 9 Section 10.4


def load_points(path: Path, version: str, url: str) -> list[tuple[int, float, float]]:
    nodes = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().lstrip("\x1e")
            if not line:
                continue
            f = json.loads(line)
            p = f["properties"]
            if p.get("@type") == "node" and p.get("place") in PLACE_KINDS:
                nodes.append((p["@id"], *f["geometry"]["coordinates"]))
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE TEMP TABLE pts (id bigint, x float8, y float8)"))
        conn.execute(text("INSERT INTO pts VALUES (:id, :x, :y)"), [{"id": i, "x": x, "y": y} for i, x, y in nodes])
        inside = conn.execute(text("""SELECT p.id, p.x, p.y FROM pts p JOIN service_areas s
            ON s.service_area_version = :v AND s.area_type = 'URBAN'
            AND ST_Intersects(s.geom, ST_SetSRID(ST_MakePoint(p.x, p.y), 4326)) ORDER BY p.id"""),
            {"v": version}).all()
    pts = [(int(i), float(x), float(y)) for i, x, y in inside]
    return sorted(random.Random(SEED).sample(pts, min(N_POINTS, len(pts))))


def table(base_url: str, pts: list[tuple[int, float, float]]) -> dict[str, list[list[float | None]]]:
    coords = ";".join(f"{x:.6f},{y:.6f}" for _, x, y in pts)
    body = httpx.get(f"{base_url}/table/v1/driving/{coords}", params={"annotations": "distance,duration"},
                     headers={"Connection": "close"}, timeout=120).json()
    if body.get("code") != "Ok":
        raise SystemExit(f"OSRM table failed: {body.get('code')}")
    return {"distance": body["distances"], "duration": body["durations"]}


def summarise(t: dict[str, list[list[float | None]]], lo: float, hi: float) -> dict[str, Any]:
    km, minutes = [], []
    n = len(t["distance"])
    for i in range(n):
        for j in range(n):
            d, s = t["distance"][i][j], t["duration"][i][j]
            if i != j and d is not None and s is not None and lo <= d / 1000 <= hi:
                km.append(d / 1000)
                minutes.append(s / 60)
    if not minutes:
        return {"pairs": 0}
    q = statistics.quantiles(minutes, n=4)
    return {"pairs": len(minutes), "median_km": round(statistics.median(km), 3),
            "median_min": round(statistics.median(minutes), 2), "p25_min": round(q[0], 2), "p75_min": round(q[2], 2),
            "median_kmh": round(statistics.median(k / (m / 60) for k, m in zip(km, minutes, strict=True)), 2)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--places", type=Path, default=Path("/osm/service_area/places.geojsonseq"))
    args = parser.parse_args()
    settings = get_settings()
    pts = load_points(args.places, args.version, settings.database_url)
    out: dict[str, Any] = {"service_area_version": args.version, "points": len(pts), "seed": SEED,
                           "place_kinds": PLACE_KINDS, "osrm": "v5.27.1 (P0 extract; car.lua / motorbike.lua)",
                           "profiles": {}}
    for profile, url in (("car", settings.osrm_car_url), ("motorbike", settings.osrm_motorbike_url)):
        t = table(url, pts)
        bands = {name: summarise(t, lo, hi) for name, (lo, hi) in BANDS_KM.items()}
        control = bands["14"].get("median_min")
        bands["14"]["revision9_min"] = R9_14KM_MIN[profile]
        if control:
            bands["14"]["revision9_over_osrm"] = round(R9_14KM_MIN[profile] / control, 3)
        out["profiles"][profile] = bands
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
