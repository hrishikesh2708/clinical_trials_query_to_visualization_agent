import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "capture_raw_dumps.py"


def test_capture_script_help_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Capture raw ClinicalTrials.gov API responses" in result.stdout


def test_capture_script_dry_run_lists_scenarios() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "studies_pembrolizumab" in result.stdout
    assert "enums" in result.stdout
    assert "metadata" in result.stdout
    assert "search_areas" in result.stdout
    assert "Dry run complete" in result.stdout
