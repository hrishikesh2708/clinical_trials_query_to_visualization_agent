"""Fixture loading helpers for tests and offline development."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "api"


def load_fixture(stem: str) -> dict[str, Any]:
    path = API_FIXTURES_DIR / f"{stem}.json"
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Fixture {stem} must be a JSON object")
    return payload


def load_fixture_studies(stem: str) -> list[dict[str, Any]]:
    payload = load_fixture(stem)
    studies = payload.get("studies")
    if not isinstance(studies, list):
        raise ValueError(f"Fixture {stem} is missing studies list")
    return studies
