"""Survey S1 service - DRAFT (owner decision P1-D5: development only, not released).

The dataset (TEST / RESEARCH) is fixed by server configuration, never by the
request. RESEARCH collection is refused until the owner releases the survey
(SURVEY_S1_RELEASED), so development data cannot mix with research data.
"""

import csv
import hashlib
import hmac
import io
import math
import time
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.settings import Settings
from app.modules.ml_models.models import SurveyRespondent, SurveyResponse
from app.modules.ml_models.survey_design import N_BLOCKS, build_design
from app.modules.ml_models.survey_schemas import StartIn, SubmitIn

GROUP_CODES = {"STUDENT": "STUDENT", "WORKER": "WORKER"}


@lru_cache
def load_questionnaire(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def questionnaire_version(q: dict[str, Any]) -> str:
    return f"{q['survey_id']}-draft-{q['draft_version']}"


def _minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _token_mac(secret: str, respondent_id: uuid.UUID, start_ms: int) -> str:
    msg = f"s1-start|{respondent_id}|{start_ms}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()[:32]


def start_token(secret: str, respondent_id: uuid.UUID, start_ms: int) -> str:
    """Signed start time kept by the browser, so the database never stores a
    timestamp finer than the minute; only the duration is kept (QC2)."""
    return f"{start_ms}.{_token_mac(secret, respondent_id, start_ms)}"


def duration_from_token(secret: str, respondent_id: uuid.UUID, token: str, now_ms: int) -> int:
    start_ms, _, mac = token.partition(".")
    if not start_ms.isdigit() or not hmac.compare_digest(mac, _token_mac(secret, respondent_id, int(start_ms))):
        raise ApiError(422, "INVALID_START_TOKEN", "The survey session token is invalid")
    return max(0, (now_ms - int(start_ms)) // 1000)


def group_cap(q: dict[str, Any]) -> int:
    """Survey decision 8: a group is closed once it holds max share x target valid answers."""
    quotas = q["quotas"]
    return math.floor(quotas["group_share"]["max"] * quotas["target_valid_respondents"])


def _require_collectable(settings: Settings) -> None:
    if settings.survey_dataset == "RESEARCH" and not settings.survey_s1_released:
        raise ApiError(403, "SURVEY_NOT_RELEASED",
                       "Research data collection is disabled until the owner releases survey S1")


def start_session(session: Session, settings: Settings, body: StartIn) -> tuple[SurveyRespondent, str]:
    _require_collectable(settings)
    q = load_questionnaire(Path(settings.survey_s1_questionnaire_path))
    completed_in_group = session.scalar(select(func.count()).select_from(SurveyRespondent).where(
        SurveyRespondent.dataset == settings.survey_dataset, SurveyRespondent.respondent_group == body.group,
        SurveyRespondent.completed_at.is_not(None))) or 0
    if completed_in_group >= group_cap(q):
        raise ApiError(409, "QUOTA_FULL_FOR_GROUP",
                       "Cảm ơn bạn! Nhóm của bạn đã đủ số câu trả lời cần thiết.", {"group": body.group})
    count = session.scalar(select(func.count()).select_from(SurveyRespondent)
                           .where(SurveyRespondent.dataset == settings.survey_dataset)) or 0
    respondent_id = uuid.uuid4()
    block = count % N_BLOCKS
    now_ms = _now_ms()
    respondent = SurveyRespondent(
        respondent_id=respondent_id, dataset=settings.survey_dataset, survey_id=q["survey_id"],
        questionnaire_version=questionnaire_version(q), design_block=block,
        design_json=build_design(q, respondent_id, block), respondent_group=body.group,
        started_at=_minute(datetime.fromtimestamp(now_ms / 1000, UTC)),
    )
    session.add(respondent)
    session.commit()
    return respondent, start_token(settings.jwt_secret, respondent_id, now_ms)


def submit(session: Session, settings: Settings, respondent_id: uuid.UUID, body: SubmitIn) -> SurveyRespondent:
    _require_collectable(settings)
    respondent = session.get(SurveyRespondent, respondent_id, with_for_update=True)
    if respondent is None or respondent.dataset != settings.survey_dataset:
        raise ApiError(404, "NOT_FOUND", "Survey session not found")
    if respondent.completed_at is not None:
        raise ApiError(409, "ALREADY_SUBMITTED", "This survey session was already submitted")
    now_ms = _now_ms()
    duration_s = duration_from_token(settings.jwt_secret, respondent_id, body.start_token, now_ms)
    design = respondent.design_json
    tasks = {t["task_id"]: t for t in design["tasks"]}
    choices = {c.task_id: c.chosen for c in body.choices}
    if set(choices) != set(tasks) or len(body.choices) != len(tasks):
        raise ApiError(422, "INCOMPLETE_CHOICES", "Every choice task must be answered exactly once")
    for task_id, chosen in choices.items():
        if chosen not in {card["alternative"] for card in tasks[task_id]["cards"]}:
            raise ApiError(422, "INVALID_CHOICE", f"{chosen} is not an option of {task_id}")
    labels = {f["display_label"] for f in design["fairness"]}
    ratings = {r.display_label: r.likert for r in body.fairness}
    if set(ratings) != labels or len(body.fairness) != len(labels) or body.preferred_label not in labels:
        raise ApiError(422, "INCOMPLETE_FAIRNESS", "Rate every method once and pick one preferred method")

    for task_id, chosen in choices.items():
        session.add(SurveyResponse(respondent_id=respondent_id, part=tasks[task_id]["part"], item_id=task_id,
                                   answer_json={"chosen": chosen}))
    for label, likert in ratings.items():
        session.add(SurveyResponse(respondent_id=respondent_id, part="2", item_id=f"H4-{label}",
                                   answer_json={"likert": likert, "preferred": label == body.preferred_label}))
    respondent.demographics_json = body.demographics.model_dump()
    respondent.completed_at = _minute(datetime.fromtimestamp(now_ms / 1000, UTC))
    respondent.duration_s = duration_s
    q = load_questionnaire(Path(settings.survey_s1_questionnaire_path))
    qc2 = q["quality_rules"]["QC2"]
    respondent.quality_flags = quality_flags(design, choices, ratings, duration_s,
                                             int(qc2["flag_below_seconds"]), str(qc2["flag"]))
    session.commit()
    return respondent


def quality_flags(design: dict[str, Any], choices: dict[str, str], ratings: dict[str, int],
                  duration_s: int, qc2_below_s: int, qc2_flag: str = "FAST_RESPONSE_REVIEW") -> list[str]:
    """QC2 / QC3 / QC4 of SURVEY_S1_DESIGN_REVIEW - flags only, nothing is discarded
    (survey decision 7: a short completion time is flagged, never auto-excluded;
    the rule is published in the questionnaire before collection)."""
    flags = []
    if duration_s < qc2_below_s:
        flags.append(qc2_flag)
    positions = [next(c["position"] for c in t["cards"] if c["alternative"] == choices[t["task_id"]])
                 for t in design["tasks"] if t["part"] == "1A"]
    if len(set(positions)) == 1:
        flags.append("QC3_SAME_POSITION_ALL_1A")
    if len(set(ratings.values())) == 1:
        flags.append("QC4_SAME_LIKERT_ALL_METHODS")
    return flags


# --- export (Phase 7-8 analysis format, survey/s1/export_schema.md) ---------------------------


def _csv(rows: list[dict[str, Any]], columns: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="raise")
    writer.writeheader()
    for row in rows:
        writer.writerow({c: row.get(c) for c in columns})
    return buf.getvalue()


RESPONDENT_COLUMNS = ["respondent_id", "questionnaire_version", "design_block", "group",
                      "ride_hailing_trips_per_week", "usual_trip_distance", "intercity_trips_per_month",
                      "started_at_utc", "completed_at_utc", "duration_s", "quality_flags"]
CHOICE_COLUMNS = ["respondent_id", "part", "task_index", "task_id", "distance_km", "weather", "urgency",
                  "alternative", "position", "price_vnd", "quote_cap_vnd", "max_price_if_unmatched_vnd", "travel_min",
                  "max_detour_min", "match_likelihood", "fill_likelihood", "walk_m", "chosen"]
FAIRNESS_COLUMNS = ["respondent_id", "method", "display_label", "display_position", "likert_fairness", "preferred"]


def export_table(session: Session, dataset: str, table: str) -> str:
    respondents = list(session.scalars(select(SurveyRespondent).where(
        SurveyRespondent.dataset == dataset, SurveyRespondent.completed_at.is_not(None))
        .order_by(SurveyRespondent.started_at, SurveyRespondent.respondent_id)))
    answers: dict[uuid.UUID, dict[str, Any]] = {}
    for r in session.scalars(select(SurveyResponse).where(
            SurveyResponse.respondent_id.in_([x.respondent_id for x in respondents]))):
        answers.setdefault(r.respondent_id, {})[r.item_id] = r.answer_json
    if table == "respondents":
        rows = [{"respondent_id": r.respondent_id, "questionnaire_version": r.questionnaire_version,
                 "design_block": r.design_block, "group": r.respondent_group, **(r.demographics_json or {}),
                 "started_at_utc": r.started_at.isoformat(), "completed_at_utc": r.completed_at.isoformat(),
                 "duration_s": r.duration_s, "quality_flags": "|".join(r.quality_flags or [])} for r in respondents]
        return _csv(rows, RESPONDENT_COLUMNS)
    if table == "choices":
        rows = []
        for r in respondents:
            for task in r.design_json["tasks"]:
                chosen = answers[r.respondent_id][task["task_id"]]["chosen"]
                for card in task["cards"]:
                    rows.append({"respondent_id": r.respondent_id, "part": task["part"], "task_index": task["task_index"],
                                 "task_id": task["task_id"], **task.get("context", {}),
                                 **{k: v for k, v in card.items() if k in CHOICE_COLUMNS},
                                 "chosen": int(card["alternative"] == chosen)})
        return _csv(rows, CHOICE_COLUMNS)
    if table == "fairness_h4":
        rows = []
        for r in respondents:
            for f in r.design_json["fairness"]:
                a = answers[r.respondent_id][f"H4-{f['display_label']}"]
                rows.append({"respondent_id": r.respondent_id, "method": f["method"].upper(),
                             "display_label": f["display_label"], "display_position": f["display_position"],
                             "likert_fairness": a["likert"], "preferred": int(a["preferred"])})
        return _csv(rows, FAIRNESS_COLUMNS)
    raise ApiError(404, "UNKNOWN_TABLE", f"Unknown export table {table}")


def quota(session: Session, dataset: str, settings: Settings) -> dict[str, Any]:
    rows = dict(session.execute(select(SurveyRespondent.respondent_group, func.count())
                                .where(SurveyRespondent.dataset == dataset, SurveyRespondent.completed_at.is_not(None))
                                .group_by(SurveyRespondent.respondent_group)).tuples().all())
    total = sum(rows.values())
    q = load_questionnaire(Path(settings.survey_s1_questionnaire_path))["quotas"]
    questionnaire = load_questionnaire(Path(settings.survey_s1_questionnaire_path))
    cap = group_cap(questionnaire)
    return {"dataset": dataset, "completed": total, "by_group": rows,
            "share_by_group": {g: round(n / total, 4) for g, n in rows.items()} if total else {},
            "group_share_band": q["group_share"], "target_valid_respondents": q["target_valid_respondents"],
            "group_cap": cap, "closed_groups": sorted(g for g, n in rows.items() if n >= cap)}


def demographics_options(settings: Settings) -> dict[str, Any]:
    q = load_questionnaire(Path(settings.survey_s1_questionnaire_path))
    return {k: {"question": v["question"], "options": v["options"]}
            for k, v in q["part_3_demographics"].items() if k != "group"}


def delete_respondent(session: Session, respondent_id: uuid.UUID) -> None:
    respondent = session.get(SurveyRespondent, respondent_id)
    if respondent is None:
        raise ApiError(404, "NOT_FOUND", "Survey session not found")
    session.delete(respondent)  # survey_responses rows cascade (FK ON DELETE CASCADE)
    session.commit()
