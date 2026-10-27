from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    # Unknown fields (e.g. name, email, phone) are rejected: nothing beyond the
    # questionnaire can be stored (Section 59.2).
    model_config = ConfigDict(extra="forbid")


class StartIn(_Strict):
    """D1 is asked before the first task so the group quota can be applied at
    session start (survey decision 8)."""

    group: Literal["STUDENT", "WORKER"]


class ChoiceIn(_Strict):
    task_id: str = Field(max_length=64)
    chosen: str = Field(max_length=32)


class FairnessIn(_Strict):
    display_label: Literal["X", "Y", "Z"]
    likert: int = Field(ge=1, le=5)


class DemographicsIn(_Strict):
    """D2-D4: non-overlapping bins of owner decision SURVEY-04 (codes in
    survey/s1/questionnaire.draft.yaml part_3_demographics); each may be skipped."""

    ride_hailing_trips_per_week: Literal["0", "1", "2-3", "4-6", "7+"] | None = None
    usual_trip_distance: Literal["LT3", "3-LT6", "6-LT10", "10-LT20", "20+"] | None = None
    intercity_trips_per_month: Literal["0", "1", "2-3", "4+"] | None = None


class SubmitIn(_Strict):
    start_token: str = Field(max_length=128)
    choices: list[ChoiceIn] = Field(max_length=20)
    fairness: list[FairnessIn] = Field(max_length=3)
    preferred_label: Literal["X", "Y", "Z"]
    demographics: DemographicsIn = DemographicsIn()
