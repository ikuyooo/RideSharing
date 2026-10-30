"""Summarise P2 benchmark runs (docs/implementation/evidence/p2_runs/*/result.json) into the
before / after tables of P2_PROGRESS_REPORT.md. Reads only; never changes a run folder.

Usage (repo root): python -I scripts/p2_runs_summary.py <label-prefix> [<label-prefix> ...]
"""

import json
import statistics
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parents[1] / "docs" / "implementation" / "evidence" / "p2_runs"
CONFIGS = ["50x0", "200x0", "1000x0", "200x10", "200x20", "1000x20"]
STAGES = ["postgis_drivers", "plan_lookup", "plan_riders", "pricing_params", "osrm_car", "osrm_motorbike",
          "convert_car", "osrm_wall", "check_all", "insertion_pool_plans", "candidate_records", "constraints",
          "persist", "total"]


def load(prefix: str) -> list[tuple[str, dict]]:
    out = []
    for d in sorted(RUNS.glob(f"*-{prefix}*")):
        f, m = d / "result.json", d / "manifest.json"
        if f.is_file() and m.is_file() and json.loads(m.read_text(encoding="utf-8"))["exit_code"] == 0:
            out.append((d.name, json.loads(f.read_text(encoding="utf-8"))))
    return out


def main() -> None:
    for prefix in sys.argv[1:]:
        runs = load(prefix)
        print(f"## {prefix}: {len(runs)} runs ({', '.join(n for n, _ in runs)})")
        print("| Workload | p50 (per run) | p95 (per run) | p99 (per run) | worst p95 | OSRM calls | errors |")
        print("|---|---|---|---|---|---|---|")
        for cfg in CONFIGS:
            rows = [c for _, r in runs for c in r["configs"] if c["config"] == cfg]
            if not rows:
                continue
            p50 = [c["generation_total_ms"]["p50"] for c in rows]
            p95 = [c["generation_total_ms"]["p95"] for c in rows]
            p99 = [c["generation_total_ms"]["p99"] for c in rows]
            calls = sorted({x for c in rows for x in c["osrm_requests_per_run"]})
            errors = sum(sum(c["errors"].values()) for c in rows)
            print(f"| {cfg} | {' / '.join(map(str, p50))} | {' / '.join(map(str, p95))} | {' / '.join(map(str, p99))} "
                  f"| {max(p95)} | {calls} | {errors} |")
        print()
        print("Stage p95 (median over runs), 200x20 and 1000x20:")
        for cfg in ("200x20", "1000x20"):
            rows = [c for _, r in runs for c in r["configs"] if c["config"] == cfg]
            parts = []
            for st in STAGES:
                vals = [c["stages_ms"][st]["p95"] for c in rows if st in c["stages_ms"]]
                if vals:
                    parts.append(f"{st}={statistics.median(vals):.1f}")
            print(f"- {cfg}: " + ", ".join(parts))
        print()


if __name__ == "__main__":
    main()
