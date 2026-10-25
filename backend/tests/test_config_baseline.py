"""Guards config/mvp_config_baseline_v1.yaml against drift from the locked document."""

import re
from pathlib import Path

import pytest
import yaml

from app.core.config_baseline import ConfigBaselineError, load_config_baseline

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = REPO_ROOT / "config" / "mvp_config_baseline_v1.yaml"
BASELINE_DOC = REPO_ROOT / "docs" / "pre" / "mvp_config_baseline_v1.md"


def _yaml_block_from_doc() -> dict:
    blocks = re.findall(r"```yaml\n(.*?)```", BASELINE_DOC.read_text(encoding="utf-8"), re.S)
    assert len(blocks) == 1, "baseline document must contain exactly one yaml block"
    return yaml.safe_load(blocks[0])


def test_config_file_matches_locked_document_exactly() -> None:
    assert yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) == _yaml_block_from_doc()


def test_loader_returns_read_only_mapping() -> None:
    cfg = load_config_baseline(CONFIG_FILE)
    assert cfg["pricing_version"] == "price_v9_two_sided_bounded"
    assert cfg["booking_and_concurrency"]["escrow_base_unit"] == "VND"
    with pytest.raises(TypeError):
        cfg["pricing_version"] = "tampered"  # type: ignore[index]


def test_loader_rejects_wrong_version(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text('config_baseline_version: "OTHER"\nconfig_status: "LOCKED_AND_APPROVED"\n')
    with pytest.raises(ConfigBaselineError):
        load_config_baseline(bad)


def test_loader_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigBaselineError):
        load_config_baseline(tmp_path / "missing.yaml")
