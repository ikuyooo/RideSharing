#!/bin/sh
# Back up ONLY the survey S1 tables (survey_respondents, survey_responses) of one
# database, as a pg_dump custom archive + SHA-256. Runs inside the postgres
# container; the archive holds anonymous data only (no identity tables).
#
# Usage (from the repo root):
#   docker compose exec -T postgres sh -s -- <database> <out_dir> < scripts/survey/backup_survey.sh
# The out_dir must be a mounted, access-restricted location on the survey server.
set -eu

DB=${1:?database}
OUT=${2:?out dir}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
FILE="$OUT/s1_${DB}_${STAMP}.dump"
mkdir -p "$OUT"

pg_dump -U "${POSTGRES_USER:-ridesharing}" -d "$DB" --format=custom --no-owner --no-privileges \
    --table=survey_respondents --table=survey_responses --file="$FILE"
sha256sum "$FILE" > "$FILE.sha256"
psql -U "${POSTGRES_USER:-ridesharing}" -d "$DB" -Atc \
    "SELECT 'rows', (SELECT count(*) FROM survey_respondents), (SELECT count(*) FROM survey_responses)" > "$FILE.counts"
echo "[survey-backup] $FILE ($(cut -d' ' -f1 "$FILE.sha256")) $(cat "$FILE.counts")"
