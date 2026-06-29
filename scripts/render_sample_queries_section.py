#!/usr/bin/env python3
"""Render the Sample queries README section from manifest.json."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "examples/live/sample_queries/manifest.json"
RENDER_SCRIPT = PROJECT_ROOT / "scripts/render_readme_example.py"

HORIZON_LABELS = {
    "time_trend": "Time trend",
    "distribution": "Distribution",
    "comparison": "Comparison",
}


def render_entry(entry: dict) -> str:
    cmd = [
        sys.executable,
        str(RENDER_SCRIPT),
        "--title",
        entry["title"],
        "--curl",
        entry["curl"],
    ]
    if json_path := entry.get("json"):
        cmd.extend(["--json", str(PROJECT_ROOT / json_path)])
    else:
        cmd.append("--curl-only")

    return subprocess.check_output(cmd, text=True).strip()


def main() -> None:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[entry["horizon"]].append(entry)

    lines = [
        "## Sample queries",
        "",
        "Natural-language queries grouped by horizon.",
        "Each block is collapsible on GitHub.",
        "Entries with a captured response include a summary table",
        "and JSON preview/link.",
        "",
    ]

    for horizon in ("time_trend", "distribution", "comparison"):
        lines.append(f"### {HORIZON_LABELS[horizon]}")
        lines.append("")
        for entry in grouped[horizon]:
            lines.append(render_entry(entry))
            lines.append("")

    print("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
