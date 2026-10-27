#!/bin/sh
# Restore a survey S1 archive made by backup_survey.sh into a database that
# already has the schema (alembic head) and EMPTY survey tables, after checking
# the SHA-256; then verify the row counts recorded at backup time.
#
# Usage: docker compose exec -T postgres sh -s -- <archive> <database> < scripts/survey/restore_survey.sh
set -eu

FILE=${1:?archive}
DB=${2:?database}
U="${POSTGRES_USER:-ridesharing}"

sha256sum -c "$FILE.sha256" >/dev/null || { echo "[survey-restore] checksum mismatch"; exit 1; }
existing=$(psql -U "$U" -d "$DB" -Atc "SELECT count(*) FROM survey_respondents")
[ "$existing" = "0" ] || { echo "[survey-restore] target survey tables are not empty ($existing rows)"; exit 1; }

pg_restore -U "$U" -d "$DB" --data-only --no-owner --no-privileges --single-transaction \
    --table=survey_respondents --table=survey_responses "$FILE"

got=$(psql -U "$U" -d "$DB" -Atc \
    "SELECT 'rows', (SELECT count(*) FROM survey_respondents), (SELECT count(*) FROM survey_responses)")
want=$(cat "$FILE.counts")
[ "$got" = "$want" ] || { echo "[survey-restore] row counts differ: got $got want $want"; exit 1; }
echo "[survey-restore] OK $got"
