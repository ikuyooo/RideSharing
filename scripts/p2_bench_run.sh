#!/bin/sh
# Runs scripts/p2_benchmark.py inside the compose network and keeps EVERY run in its own
# evidence folder (never overwritten): docs/implementation/evidence/p2_runs/<run_id>/
#   manifest.json   run id, UTC start / end, git commit + dirty file count, arguments, exit code
#   result.json | explain.txt | cprofile.txt   the benchmark output
#   docker_stats.jsonl   CPU / memory of every container, sampled during the run
#   console.log     the benchmark's console output
#
# Usage (repo root, stack running):
#   MSYS_NO_PATHCONV=1 sh scripts/p2_bench_run.sh <label> [benchmark arguments ...]
set -u
LABEL=${1:?label}
shift
ROOT=$(cd "$(dirname "$0")/.." && (pwd -W 2>/dev/null || pwd))
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$LABEL"
DIR="docs/implementation/evidence/p2_runs/$RUN_ID"
mkdir -p "$DIR"
MODE=bench
for a in "$@"; do case "$a" in --mode=*) MODE=${a#--mode=} ;; esac; done
prev=""; for a in "$@"; do [ "$prev" = "--mode" ] && MODE=$a; prev=$a; done
case "$MODE" in bench) OUT=result.json ;; *) OUT=$MODE.txt ;; esac
COMMIT=$(git rev-parse HEAD)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)

(
  while [ ! -f "$DIR/.done" ]; do
    T=$(date -u +%H:%M:%S)
    docker stats --no-stream --format '{{json .}}' 2>/dev/null \
      | while read -r line; do echo "{\"t\":\"$T\",\"stats\":$line}"; done >> "$DIR/docker_stats.jsonl"
    # One sample every 10 s: back-to-back `docker stats` loads the Docker Desktop VM and is
    # suspected of disturbing the latency it observes (runs before-r1 / before-r2, 2026-10-30).
    i=0; while [ $i -lt 10 ] && [ ! -f "$DIR/.done" ]; do sleep 1; i=$((i + 1)); done
  done
) &
SAMPLER=$!

docker compose run --rm --no-deps -v "$ROOT:/repo" backend \
  python -I /repo/scripts/p2_benchmark.py --in-network --run-id "$RUN_ID" --out "/repo/$DIR/$OUT" "$@" \
  > "$DIR/console.log" 2>&1
CODE=$?
touch "$DIR/.done"
wait "$SAMPLER" 2>/dev/null
rm -f "$DIR/.done"
FINISHED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ARGS=$(printf '%s ' "$@" | sed 's/"/\\"/g')
cat > "$DIR/manifest.json" <<EOF
{
  "run_id": "$RUN_ID",
  "started_utc": "$STARTED",
  "finished_utc": "$FINISHED",
  "git_commit": "$COMMIT",
  "git_dirty_files": $DIRTY,
  "arguments": "$ARGS",
  "output": "$OUT",
  "exit_code": $CODE,
  "environment": "docker compose network: backend image + osrm-car / osrm-motorbike / postgres; synthetic data, throwaway database p2_bench"
}
EOF
grep -v "alembic.runtime" "$DIR/console.log" | tail -12
echo "run $RUN_ID exit $CODE -> $DIR"
exit $CODE
