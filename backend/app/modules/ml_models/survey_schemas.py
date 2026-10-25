from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    # Unknown fields (e.g. name, email, phone) are rejected: nothing beyond the
    # questionnaire can be stored (Section 59.2).
    model_config = ConfigDict(extra="forbid")


class ChoiceIn(_Strict):
    task_id: str = Field(max_length=64)
    chosen: str = Field(max_length=32)


class FairnessIn(_Strict):
    display_label: Literal["X", "Y", "Z"]
    likert: int = Field(ge=1, le=5)


class DemographicsIn(_Strict):
    """D2-D4 answer bins are TBD (pending owner approval); until then only null is accepted."""

    ride_hailing_trips_per_week: None = None
    usual_trip_distance: None = None
    intercity_trips_per_month: None = None


class SubmitIn(_Strict):
    group: Literal["STUDENT", "WORKER"]
    choices: list[ChoiceIn] = Field(max_length=20)
    fairness: list[FairnessIn] = Field(max_length=3)
    preferred_label: Literal["X", "Y", "Z"]
    demographics: DemographicsIn = DemographicsIn()
