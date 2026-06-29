#!/usr/bin/env python3
"""Generate submission example VisualizeResponse JSON from mocked pipeline runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio

from tests.api.horizon_mocks import ALL_SCENARIOS, run_scenario

EXAMPLES_DIR = PROJECT_ROOT / "examples"

OUTPUT_FILES = {
    "time_trend_pembrolizumab": "time_trend_pembrolizumab.json",
    "distribution_breast_cancer_phase": "distribution_breast_cancer_phase.json",
    "comparison_pembrolizumab_vs_nivolumab": (
        "comparison_pembrolizumab_vs_nivolumab.json"
    ),
    "geographic_lung_cancer_recruiting": "geographic_lung_cancer_recruiting.json",
    "network_diabetes_sponsor_drug": "network_diabetes_sponsor_drug.json",
}


async def generate_all() -> None:
    EXAMPLES_DIR.mkdir(exist_ok=True)
    for scenario in ALL_SCENARIOS:
        output_name = OUTPUT_FILES[scenario.name]
        response = await run_scenario(scenario)
        output_path = EXAMPLES_DIR / output_name
        output_path.write_text(
            json.dumps(response.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {output_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    asyncio.run(generate_all())


if __name__ == "__main__":
    main()
