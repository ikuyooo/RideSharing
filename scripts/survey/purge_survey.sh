#!/bin/sh
# Retention end (proposed: 12 months after the survey closes - an owner policy, not a
# statutory period): delete every survey S1 row of ONE dataset from ONE database
# (survey_responses go with their respondents via ON DELETE CASCADE) and print the
# counts for the deletion log. Backups older than the retention end must be deleted
# with it (see SURVEY_S1_DEPLOYMENT_PLAN.md, retention).
#
# Usage: docker compose exec -T postgres sh -s -- <database> <TEST|RESEARCH> <confirm-word> < scripts/survey/purge_survey.sh
#   confirm-word must be "PURGE-<dataset>" to avoid accidental runs.
set -eu

DB=${1:?database}
DATASET=${2:?dataset}
CONFIRM=${3:?confirm word}
U="${POSTGRES_USER:-ridesharing}"
[ "$CONFIRM" = "PURGE-$DATASET" ] || { echo "[survey-purge] confirmation word must be PURGE-$DATASET"; exit 1; }
case "$DATASET" in TEST|RESEARCH) ;; *) echo "[survey-purge] dataset must be TEST or RESEARCH"; exit 1;; esac

psql -U "$U" -d "$DB" -v ON_ERROR_STOP=1 -At <<SQL
BEGIN;
SELECT 'before', (SELECT count(*) FROM survey_respondents WHERE dataset = '$DATASET'),
       (SELECT count(*) FROM survey_responses r JOIN survey_respondents p USING (respondent_id) WHERE p.dataset = '$DATASET');
DELETE FROM survey_respondents WHERE dataset = '$DATASET';
SELECT 'after', (SELECT count(*) FROM survey_respondents WHERE dataset = '$DATASET'),
       (SELECT count(*) FROM survey_responses r JOIN survey_respondents p USING (respondent_id) WHERE p.dataset = '$DATASET');
COMMIT;
SQL
echo "[survey-purge] $DATASET rows deleted from $DB at $(date -u +%Y-%m-%dT%H:%M:%SZ) - record this line in the deletion log"
