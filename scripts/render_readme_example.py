#!/usr/bin/env python3
"""Render a collapsible README example block from a curl command and JSON response."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_INLINE_THRESHOLD = 8_000
PREVIEW_LINES = 40


def load_response(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "detail" in payload:
        detail = payload["detail"]
        code = detail.get("code", "error")
        message = detail.get("message", "Request failed")
        raise SystemExit(f"{path}: API error ({code}): {message}")
    return payload


def summarize(payload: dict) -> dict[str, str]:
    viz = payload.get("visualization", {})
    meta = payload.get("meta", {})
    viz_type = viz.get("type", "—")
    data = viz.get("data") or []
    nodes = viz.get("nodes") or []
    edges = viz.get("edges") or []
    if viz_type == "network_graph" and isinstance(data, dict):
        nodes = data.get("nodes") or nodes
        edges = data.get("edges") or edges

    if viz_type == "network_graph":
        datum_label = f"{len(nodes)} nodes, {len(edges)} edges"
    else:
        datum_label = f"{len(data)} data rows"

    filters = meta.get("filters") or {}
    active_filters = [
        f"{key}={value}"
        for key, value in filters.items()
        if value is not None
    ]

    return {
        "viz_type": viz_type,
        "title": meta.get("title") or "—",
        "datum_label": datum_label,
        "studies": str(meta.get("total_studies_fetched", "—")),
        "granularity": meta.get("time_granularity") or "—",
        "filters": ", ".join(active_filters) if active_filters else "none",
    }


def render_summary_table(summary: dict[str, str]) -> str:
    rows = [
        ("Visualization", summary["viz_type"]),
        ("Title", summary["title"]),
        ("Data", summary["datum_label"]),
        ("Studies fetched", summary["studies"]),
        ("Time granularity", summary["granularity"]),
        ("Filters applied", summary["filters"]),
    ]
    lines = [
        "| Field | Value |",
        "|-------|-------|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def render_json_section(
    json_path: Path,
    payload: dict,
    *,
    inline_threshold: int,
) -> list[str]:
    serialized = json.dumps(payload, indent=2)
    size = len(serialized.encode("utf-8"))
    rel_path = json_path.as_posix()
    lines = ["**Full response**", ""]

    if size <= inline_threshold:
        lines.extend(
            [
                "<details>",
                "<summary>JSON (click to expand)</summary>",
                "",
                "```json",
                serialized,
                "```",
                "",
                "</details>",
            ]
        )
        return lines

    preview = "\n".join(serialized.splitlines()[:PREVIEW_LINES])
    lines.extend(
        [
            f"Saved to [`{rel_path}`]({rel_path}) ({size:,} bytes).",
            "",
            "<details>",
            "<summary>Preview (first 40 lines)</summary>",
            "",
            "```json",
            preview,
            "...",
            "```",
            "",
            "</details>",
        ]
    )
    return lines


def render_request_only(*, title: str, curl: str) -> str:
    return "\n".join(
        [
            "<details>",
            f"<summary><strong>{title}</strong></summary>",
            "",
            "**Request**",
            "",
            "```bash",
            curl.strip(),
            "```",
            "",
            "**Response**",
            "",
            "_Capture with the curl above, save JSON, then re-render with "
            "`scripts/render_readme_example.py --json <path>`._",
            "",
            "</details>",
        ]
    )


def render_block(
    *,
    title: str,
    curl: str,
    json_path: Path,
    inline_threshold: int,
) -> str:
    payload = load_response(json_path)
    summary = summarize(payload)
    summary_line = (
        f"{title} — {summary['viz_type']}, "
        f"{summary['datum_label']}, "
        f"{summary['studies']} studies"
    )

    sections = [
        "<details>",
        f"<summary><strong>{summary_line}</strong></summary>",
        "",
        "**Request**",
        "",
        "```bash",
        curl.strip(),
        "```",
        "",
        "**Response summary**",
        "",
        render_summary_table(summary),
        "",
        *render_json_section(json_path, payload, inline_threshold=inline_threshold),
        "",
        "</details>",
    ]
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a collapsible README example from curl + JSON response.",
    )
    parser.add_argument("--title", required=True, help="Short label shown in summary")
    parser.add_argument(
        "--curl",
        help="curl command string (use --curl-file for multiline commands)",
    )
    parser.add_argument(
        "--curl-file",
        type=Path,
        help="Path to a file containing the curl command",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Path to VisualizeResponse JSON (omit with --curl-only)",
    )
    parser.add_argument(
        "--curl-only",
        action="store_true",
        help="Render request-only block without a captured response",
    )
    parser.add_argument(
        "--inline-threshold",
        type=int,
        default=DEFAULT_INLINE_THRESHOLD,
        help="Inline full JSON when response is at or below this many bytes",
    )
    args = parser.parse_args()

    if args.curl_file:
        curl = args.curl_file.read_text(encoding="utf-8")
    elif args.curl:
        curl = args.curl
    else:
        raise SystemExit("Provide --curl or --curl-file")

    if args.curl_only:
        if args.json:
            raise SystemExit("--curl-only cannot be combined with --json")
        print(render_request_only(title=args.title, curl=curl))
        return

    if not args.json:
        raise SystemExit("Provide --json or use --curl-only")

    print(
        render_block(
            title=args.title,
            curl=curl,
            json_path=args.json,
            inline_threshold=args.inline_threshold,
        )
    )


if __name__ == "__main__":
    main()
