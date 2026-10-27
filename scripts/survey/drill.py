"""Helper of backup_restore_drill.sh (runs in the backend image: alembic + psycopg).

prepare : create two throwaway databases at alembic head; put SYNTHETIC TEST
          rows (3 respondents x 10 responses) into the source database.
verify  : compare a content hash of both databases' survey tables, print the
          result, then drop both databases. Exit 1 when they differ.
Never touches the main database.
"""

import hashlib
import os
import subprocess
import sys
import uuid

import psycopg

SRC, DST = "s1_drill_source", "s1_drill_restore"
BASE = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0]


def admin() -> psycopg.Connection:
    return psycopg.connect(f"{BASE}/postgres", autocommit=True)


def digest(db: str) -> tuple[int, int, str]:
    with psycopg.connect(f"{BASE}/{db}") as c:
        rows = c.execute("""SELECT r.respondent_id::text, r.dataset, r.design_block, r.duration_s,
                                   r.quality_flags::text, r.demographics_json::text, s.part, s.item_id,
                                   s.answer_json::text
                            FROM survey_respondents r JOIN survey_responses s USING (respondent_id)
                            ORDER BY 1, 8""").fetchall()
        n_r = c.execute("SELECT count(*) FROM survey_respondents").fetchone()[0]
    return n_r, len(rows), hashlib.sha256(repr(rows).encode()).hexdigest()


def prepare() -> None:
    with admin() as a:
        for db in (SRC, DST):
            a.execute(f'DROP DATABASE IF EXISTS "{db}"')
            a.execute(f'CREATE DATABASE "{db}"')
    for db in (SRC, DST):
        env = dict(os.environ, DATABASE_URL=f"{BASE.replace('postgresql://', 'postgresql+psycopg://')}/{db}")
        subprocess.run(["alembic", "upgrade", "head"], check=True, env=env, capture_output=True)
    with psycopg.connect(f"{BASE}/{SRC}") as c:
        for i in range(3):
            rid = uuid.uuid4()
            c.execute("""INSERT INTO survey_respondents (respondent_id, dataset, survey_id, questionnaire_version,
                         design_block, design_json, respondent_group, demographics_json, started_at, completed_at,
                         quality_flags, duration_s)
                         VALUES (%s, 'TEST', 's1', 's1-drill', %s, '{"synthetic": true}', 'STUDENT',
                         '{"usual_trip_distance": "3-LT7"}', date_trunc('minute', now()), date_trunc('minute', now()),
                         ARRAY['QC2_FAST_COMPLETION'], 90)""", (rid, i))
            for k in range(10):
                c.execute("INSERT INTO survey_responses (respondent_id, part, item_id, answer_json) "
                          "VALUES (%s, '1A', %s, '{\"chosen\": \"BIKE_URBAN\"}')", (rid, f"task-{k}"))
    print(f"[survey-drill] prepared {SRC} {digest(SRC)} and empty {DST} {digest(DST)}")


def verify() -> None:
    src, dst = digest(SRC), digest(DST)
    with admin() as a:
        for db in (SRC, DST):
            a.execute(f'DROP DATABASE "{db}"')
    print(f"[survey-drill] source  {src}\n[survey-drill] restore {dst}")
    if src != dst or src[0] == 0:
        sys.exit("[survey-drill] FAIL: restored content differs")
    print(f"[survey-drill] PASS: {src[0]} respondents / {src[1]} responses restored identically; drill databases dropped")


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()
