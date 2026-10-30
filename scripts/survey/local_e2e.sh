#!/bin/sh
# Local end-to-end run of the WHOLE survey S1 pipeline (owner "DEVELOPMENT FIRST,
# DEPLOYMENT LATER"): a separate backend container (real uvicorn, real Redis guard and
# rejection counters on Redis database 15) on a THROWAWAY database, dataset TEST,
# 150 synthetic respondents + abandoned sessions + rejected submissions, admin export
# and MNL estimation from the export. The start / submit limits are raised for this run
# only, because every synthetic respondent comes from one address.
# Everything created here is removed at the end; the main database is checked untouched.
# Synthetic answers test the pipeline - they are NOT survey results.
#
# Usage (repo root, stack running): MSYS_NO_PATHCONV=1 sh scripts/survey/local_e2e.sh <python with httpx> [evidence.json]
set -eu

PY=${1:?python interpreter with httpx}
HERE=$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))
ROOT=$(cd "$(dirname "$0")/../.." && (pwd -W 2>/dev/null || pwd))
OUT=${2:-$ROOT/docs/implementation/survey/evidence/s1_local_e2e.json}
set -a; . ./.env; set +a
DB=s1_local_e2e
PORT=8097
ADMIN_EMAIL=local-e2e-admin@example.org
ADMIN_PASSWORD=$(od -An -N12 -tx1 /dev/urandom | tr -d ' \n')
REDIS_E2E="redis://:$REDIS_PASSWORD@redis:6379/15"
redis_clear() {
  docker compose exec -T redis sh -c "redis-cli -a \"\$REDIS_PASSWORD\" -n 15 --no-auth-warning --scan --pattern 's1:*' \
    | xargs -r redis-cli -a \"\$REDIS_PASSWORD\" -n 15 --no-auth-warning del" >/dev/null 2>&1 || true
}
cleanup() {
  docker rm -f s1-local-backend >/dev/null 2>&1 || true
  docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -qc "DROP DATABASE IF EXISTS $DB" >/dev/null 2>&1 || true
  redis_clear
}
trap cleanup EXIT

main_before=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM survey_respondents")
redis_clear
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -qc "DROP DATABASE IF EXISTS $DB" -c "CREATE DATABASE $DB"
E2E_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$DB"
docker compose run --rm --no-deps -T -e DATABASE_URL="$E2E_URL" backend alembic upgrade head >/dev/null 2>&1
docker compose run --rm --no-deps -T -e DATABASE_URL="$E2E_URL" -e ADMIN_PASSWORD="$ADMIN_PASSWORD" backend \
  python -m app.modules.identity.cli create-admin --email "$ADMIN_EMAIL" >/dev/null
docker compose run -d --no-deps --name s1-local-backend -p "127.0.0.1:$PORT:8000" \
  -e DATABASE_URL="$E2E_URL" -e REDIS_URL="$REDIS_E2E" -e SURVEY_DATASET=TEST -e SURVEY_S1_RELEASED=false \
  -e SURVEY_RATE_LIMIT_STARTS_PER_HOUR=1000 -e SURVEY_RATE_LIMIT_SUBMITS_PER_HOUR=1000 backend \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null
for i in $(seq 1 60); do
  docker exec s1-local-backend python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health/live')" 2>/dev/null && break; sleep 1
done

"$PY" -I "$HERE/local_e2e_client.py" "http://127.0.0.1:$PORT" "$ADMIN_EMAIL" "$ADMIN_PASSWORD" "$OUT"

counts=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$DB" -Atc \
  "SELECT dataset || '|' || count(*) FILTER (WHERE completed_at IS NOT NULL) || '|' || count(*) FROM survey_respondents GROUP BY dataset")
main_after=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM survey_respondents")
echo "[local] throwaway DB (dataset|completed|started): $counts; main DB survey rows before/after: $main_before/$main_after"
[ "$counts" = "TEST|150|166" ] && [ "$main_before" = "$main_after" ] || { echo "[local] FAIL: dataset separation"; exit 1; }
echo "[local] PASS - container, throwaway database and Redis db 15 keys are removed now"
