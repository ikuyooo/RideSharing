"""Loader for the locked MVP configuration baseline.

The YAML file is a verbatim copy of MVP_CONFIG_BASELINE_V1.md §4. Business
modules must read parameters from here (and, from Phase 1, from the versioned
`pricing_configs` table) - never hardcode them.
"""

from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

EXPECTED_BASELINE_VERSION = "MVP_CONFIG_BASELINE_V1"
EXPECTED_STATUS = "LOCKED_AND_APPROVED"


class ConfigBaselineError(RuntimeError):
    pass


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def load_config_baseline(path: Path) -> Mapping[str, Any]:
    """Parse and sanity-check the baseline; returns a read-only mapping."""
    if not path.is_file():
        raise ConfigBaselineError(f"config baseline not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigBaselineError("config baseline must be a YAML mapping")
    if data.get("config_baseline_version") != EXPECTED_BASELINE_VERSION:
        raise ConfigBaselineError(
            f"unexpected config_baseline_version: {data.get('config_baseline_version')!r}"
        )
    if data.get("config_status") != EXPECTED_STATUS:
        raise ConfigBaselineError(f"unexpected config_status: {data.get('config_status')!r}")
    return _freeze(data)


@lru_cache
def _cached(path: Path) -> Mapping[str, Any]:
    return load_config_baseline(path)


def get_config_baseline() -> Mapping[str, Any]:
    """The baseline at CONFIG_BASELINE_PATH, parsed once per process."""
    from app.core.settings import get_settings

    return _cached(Path(get_settings().config_baseline_path))
