"""Process settings, read from environment variables (see .env.example)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str
    redis_url: str
    osrm_car_url: str
    osrm_motorbike_url: str

    config_baseline_path: Path

    dependency_timeout_s: float = 3.0

    # --- identity (Revision 9, Section 59.1) ---------------------------------
    jwt_secret: str
    access_token_ttl_s: int = 15 * 60  # "Access Token ngắn hạn (15 phút)"
    # Not specified by Revision 9; technical default.
    refresh_token_ttl_s: int = 14 * 24 * 3600

    # --- trip classification (Section 2.3; owner decisions P1-D1/D2/D3) -------
    # service_areas version used for classification. Unset -> classification
    # is unavailable (503) rather than guessed.
    service_area_version: str | None = None
    # Development only: allow classifying against CANDIDATE (not owner-approved)
    # geometry. Results obtained this way are not acceptance evidence.
    allow_candidate_service_area: bool = False
    routing_timeout_s: float = 5.0

    # --- survey S1 (P1-D5; draft, not released) -------------------------------
    survey_s1_questionnaire_path: Path = Path("/app/survey/s1/questionnaire.draft.yaml")
    # Fixed per deployment, never chosen by a request. RESEARCH also needs the
    # owner's release flag below.
    survey_dataset: Literal["TEST", "RESEARCH"] = "TEST"
    survey_s1_released: bool = False
    # Anti-spam per client address (hashed, never stored); technical defaults.
    survey_rate_limit_starts_per_hour: int = 10
    survey_rate_limit_submits_per_hour: int = 20

    @field_validator("service_area_version", mode="before")
    @classmethod
    def _empty_is_unset(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
