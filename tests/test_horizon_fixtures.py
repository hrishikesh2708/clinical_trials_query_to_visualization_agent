import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "api"
CAPTURE_SCRIPT = PROJECT_ROOT / "scripts" / "capture_horizon_fixtures.py"

ALLOWED_TOP_LEVEL_KEYS = frozenset({"studies", "nextPageToken", "totalCount"})


def _fixture_json_paths() -> list[Path]:
    return sorted(
        path
        for path in FIXTURES_DIR.glob("*.json")
        if not path.name.endswith(".meta.json")
    )


def _meta_paths() -> list[Path]:
    return sorted(FIXTURES_DIR.glob("*.meta.json"))


@pytest.mark.parametrize("fixture_path", _fixture_json_paths(), ids=lambda p: p.stem)
def test_fixture_loads_as_valid_json_with_expected_shape(fixture_path: Path) -> None:
    with fixture_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    assert isinstance(payload, dict)
    assert set(payload.keys()).issubset(ALLOWED_TOP_LEVEL_KEYS)
    assert "studies" in payload
    assert isinstance(payload["studies"], list)

    if "nextPageToken" in payload:
        assert isinstance(payload["nextPageToken"], str)
    if "totalCount" in payload:
        assert isinstance(payload["totalCount"], int)


@pytest.mark.parametrize("meta_path", _meta_paths(), ids=lambda p: p.stem)
def test_meta_sidecar_has_required_fields(meta_path: Path) -> None:
    with meta_path.open(encoding="utf-8") as handle:
        meta = json.load(handle)

    assert meta["horizon"]
    assert meta["fixture"].endswith(".json")
    assert meta["captured_at"]
    assert meta["endpoint"] == "/studies"
    assert meta["source_query"]
    assert isinstance(meta["request_params"], dict)

    fixture_path = FIXTURES_DIR / meta["fixture"]
    assert fixture_path.exists()


def test_each_fixture_has_meta_sidecar() -> None:
    fixture_names = {path.stem for path in _fixture_json_paths()}
    meta_stems = {
        path.name.removesuffix(".meta.json") for path in _meta_paths()
    }
    assert fixture_names == meta_stems


def test_at_least_one_fixture_per_horizon() -> None:
    horizons = {
        json.loads(path.read_text(encoding="utf-8"))["horizon"]
        for path in _meta_paths()
        if not path.stem.startswith("studies_")
    }
    assert horizons == {
        "time_trend",
        "distribution",
        "comparison",
        "geographic",
        "network",
    }


def test_comparison_has_two_arm_fixtures() -> None:
    comparison_meta = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in _meta_paths()
        if json.loads(path.read_text(encoding="utf-8"))["horizon"] == "comparison"
    ]
    assert len(comparison_meta) == 2
    arm_labels = {meta["arm_label"] for meta in comparison_meta}
    assert arm_labels == {"Pembrolizumab", "Nivolumab"}
    groups = {meta["comparison_group"] for meta in comparison_meta}
    assert groups == {"pembrolizumab_vs_nivolumab"}


def test_empty_fixture_has_no_studies() -> None:
    with (FIXTURES_DIR / "studies_empty.json").open(encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["studies"] == []


def test_capture_horizon_fixtures_script_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, str(CAPTURE_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Capture trimmed horizon API fixtures" in result.stdout


def test_capture_horizon_fixtures_script_dry_run_lists_fixtures() -> None:
    result = subprocess.run(
        [sys.executable, str(CAPTURE_SCRIPT), "--dry-run"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "time_trend_pembrolizumab" in result.stdout
    assert "studies_empty" in result.stdout
    assert "Dry run complete" in result.stdout
