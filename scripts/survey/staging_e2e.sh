#!/bin/sh
# Local HTTPS staging check of the survey release path (OWNER APPROVAL s.6) WITHOUT a
# public domain: the real infra/survey/Caddyfile serves "localhost" with Caddy's
# internal CA, in front of a SEPARATE staging backend on a THROWAWAY database
# (dataset TEST). One synthetic TEST response goes through HTTPS end to end; the
# client checks TLS against Caddy's root certificate, the route allow-list, IP-free
# logs, TEST / RESEARCH separation and that the main database is untouched.
# Everything created here is removed at the end. This is NOT a public release.
#
# Usage (repo root, stack running): MSYS_NO_PATHCONV=1 sh scripts/survey/staging_e2e.sh <python with httpx>
set -eu

PY=${1:?python interpreter with httpx}
HERE=$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))
ROOT=$(cd "$(dirname "$0")/../.." && (pwd -W 2>/dev/null || pwd))
set -a; . ./.env; set +a
DB=s1_stage_e2e
NET=s1stage
WORK=$(mktemp -d)
WORKW=$(cd "$WORK" && (pwd -W 2>/dev/null || pwd))   # path form Docker / Python accept on Windows
cleanup() {
  docker rm -f s1-stage-proxy s1-stage-backend >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -qc "DROP DATABASE IF EXISTS $DB" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -qc "DROP DATABASE IF EXISTS $DB" -c "CREATE DATABASE $DB"
STAGE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$DB"
docker compose run --rm --no-deps -T -e DATABASE_URL="$STAGE_URL" backend alembic upgrade head >/dev/null 2>&1
docker network create "$NET" >/dev/null
docker compose run -d --no-deps --name s1-stage-backend -e DATABASE_URL="$STAGE_URL" \
  -e SURVEY_DATASET=TEST -e SURVEY_S1_RELEASED=false backend \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*' >/dev/null
docker network connect --alias backend "$NET" s1-stage-backend
docker run -d --name s1-stage-proxy --network "$NET" -p 127.0.0.1:8443:443 \
  -e SURVEY_DOMAIN=localhost -e ACME_EMAIL=ops@example.org \
  -v "$ROOT/infra/survey/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2.8.4 >/dev/null
for i in $(seq 1 60); do
  docker exec s1-stage-proxy test -f /data/caddy/pki/authorities/local/root.crt 2>/dev/null && break; sleep 1
done
docker cp s1-stage-proxy:/data/caddy/pki/authorities/local/root.crt "$WORKW/root.crt" >/dev/null
for i in $(seq 1 60); do
  docker exec s1-stage-backend python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health/live')" 2>/dev/null && break; sleep 1
done

"$PY" -I "$HERE/staging_client.py" "$WORKW/root.crt"

echo "[stage] access log (proxy) - must contain no client address:"
docker exec s1-stage-proxy sh -c 'cat /data/logs/survey_access.log' > "$WORK/access.log"
if grep -Eq '"(remote_ip|client_ip)"|172\.[0-9]+\.[0-9]+\.[0-9]+|127\.0\.0\.1' "$WORK/access.log"; then
  echo "[stage] FAIL: client address found in proxy access log"; exit 1
fi
echo "[stage] proxy access log: $(wc -l < "$WORK/access.log") lines, no client address"
docker logs s1-stage-backend 2>&1 | grep -E '/api/survey|/survey/s1' > "$WORK/app.log" || true
if grep -Eq '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+' "$WORK/app.log"; then
  echo "[stage] FAIL: client address in backend access log for survey paths"; exit 1
fi
echo "[stage] backend survey access log: $(wc -l < "$WORK/app.log") lines, no client address"
counts=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$DB" -Atc \
  "SELECT dataset, count(*) FROM survey_respondents WHERE completed_at IS NOT NULL GROUP BY 1")
main=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM survey_respondents")
echo "[stage] staging DB completed respondents: ${counts:-none}; main DB survey rows: $main"
[ "$counts" = "TEST|1" ] && [ "$main" = "0" ] || { echo "[stage] FAIL: dataset separation"; exit 1; }
echo "[stage] PASS - staging containers, network and database are removed now"
