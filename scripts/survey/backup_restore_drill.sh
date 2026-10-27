#!/bin/sh
# Backup / restore DRILL for survey S1 on two throwaway databases with SYNTHETIC
# TEST rows - never touches the main database. Proves that an archive made the way
# backup_survey.sh makes it restores with identical content.
#
# Usage (repo root, stack running):  sh scripts/survey/backup_restore_drill.sh
# Git Bash on Windows: MSYS_NO_PATHCONV=1 sh scripts/survey/backup_restore_drill.sh
set -eu

HERE=$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))
DC="docker compose"

$DC run --rm --no-deps -T -v "$HERE:/drill:ro" --entrypoint python backend /drill/drill.py prepare

# Dump / restore with the postgres image's own client tools (same server version),
# exactly the options of backup_survey.sh / restore_survey.sh.
$DC exec -T postgres sh -c '
  set -e
  pg_dump -U "$POSTGRES_USER" -d s1_drill_source --format=custom --no-owner --no-privileges \
      --table=survey_respondents --table=survey_responses --file=/tmp/s1_drill.dump
  echo "[survey-drill] archive sha256 $(sha256sum /tmp/s1_drill.dump | cut -d" " -f1)"
  pg_restore -U "$POSTGRES_USER" -d s1_drill_restore --data-only --no-owner --no-privileges \
      --single-transaction --table=survey_respondents --table=survey_responses /tmp/s1_drill.dump
  rm /tmp/s1_drill.dump'

$DC run --rm --no-deps -T -v "$HERE:/drill:ro" --entrypoint python backend /drill/drill.py verify
