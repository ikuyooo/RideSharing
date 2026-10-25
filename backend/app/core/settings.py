"""Process settings, read from environment variables (see .env.example)."""

from functools import lru_cache
from pathlib import Path

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
