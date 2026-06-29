"""Capture trimmed horizon API fixtures for offline mapper and agent tests.

Writes stable JSON fixtures and .meta.json sidecars under tests/fixtures/api/.
Uses fields projections from horizon_spec().fields_pieces to minimize payload size.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.core.config import Settings
from app.domain.horizons import Horizon, horizon_spec
from app.infrastructure.ctgov.client import CtgovClient, ctgov_client_from_settings
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.models import StudiesSearchParams, StudiesSearchResult
from scripts.capture_raw_dumps import patch_client_urllib_transport

DEFAULT_OUTPUT_DIR = Path("tests/fixtures/api")
COMPARISON_GROUP = "pembrolizumab_vs_nivolumab"


@dataclass(frozen=True)
class FixtureSpec:
    name: str
    horizon: Horizon | None
    source_query: str
    params: StudiesSearchParams
    arm_label: str | None = None
    comparison_group: str | None = None

    @property
    def horizon_label(self) -> str:
        if self.horizon is None:
            return "any"
        return self.horizon.value


def _fields(horizon: Horizon) -> list[str]:
    return list(horizon_spec(horizon).fields_pieces)


FIXTURE_SPECS: tuple[FixtureSpec, ...] = (
    FixtureSpec(
        name="time_trend_pembrolizumab",
        horizon=Horizon.TIME_TREND,
        source_query="Trials per year for pembrolizumab since 2015",
        params=StudiesSearchParams(
            query_intr="Pembrolizumab",
            filter_advanced="AREA[StartDate]2015",
            fields=_fields(Horizon.TIME_TREND),
            page_size=15,
            count_total=True,
        ),
    ),
    FixtureSpec(
        name="distribution_breast_cancer_phase",
        horizon=Horizon.DISTRIBUTION,
        source_query="Breast cancer trials by phase",
        params=StudiesSearchParams(
            query_cond="breast cancer",
            fields=_fields(Horizon.DISTRIBUTION),
            page_size=15,
            count_total=True,
        ),
    ),
    FixtureSpec(
        name="comparison_pembrolizumab_arm",
        horizon=Horizon.COMPARISON,
        source_query="Pembrolizumab vs nivolumab trials by phase — arm 1",
        params=StudiesSearchParams(
            query_intr="Pembrolizumab",
            fields=_fields(Horizon.COMPARISON),
            page_size=15,
            count_total=True,
        ),
        arm_label="Pembrolizumab",
        comparison_group=COMPARISON_GROUP,
    ),
    FixtureSpec(
        name="comparison_nivolumab_arm",
        horizon=Horizon.COMPARISON,
        source_query="Pembrolizumab vs nivolumab trials by phase — arm 2",
        params=StudiesSearchParams(
            query_intr="Nivolumab",
            fields=_fields(Horizon.COMPARISON),
            page_size=15,
            count_total=True,
        ),
        arm_label="Nivolumab",
        comparison_group=COMPARISON_GROUP,
    ),
    FixtureSpec(
        name="geographic_pembrolizumab_countries",
        horizon=Horizon.GEOGRAPHIC,
        source_query="Countries running pembrolizumab trials",
        params=StudiesSearchParams(
            query_intr="Pembrolizumab",
            fields=_fields(Horizon.GEOGRAPHIC),
            page_size=15,
            count_total=True,
        ),
    ),
    FixtureSpec(
        name="network_diabetes_sponsor_drug",
        horizon=Horizon.NETWORK,
        source_query="Sponsor–drug–condition network for diabetes trials",
        params=StudiesSearchParams(
            query_cond="diabetes",
            fields=_fields(Horizon.NETWORK),
            page_size=15,
            count_total=True,
        ),
    ),
    FixtureSpec(
        name="studies_empty",
        horizon=None,
        source_query="Near-empty search (Stage 3 obscure query)",
        params=StudiesSearchParams(
            query_term="xyzzy_nonexistent_trial_term_12345",
            fields=["NCTId"],
            page_size=15,
        ),
    ),
    FixtureSpec(
        name="studies_single",
        horizon=None,
        source_query="Single-study pagination smoke",
        params=StudiesSearchParams(
            query_intr="Pembrolizumab",
            fields=["NCTId", "StartDateStruct"],
            page_size=1,
            count_total=True,
        ),
    ),
)

FIXTURE_NAMES = tuple(spec.name for spec in FIXTURE_SPECS)


def utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def search_result_payload(result: StudiesSearchResult) -> dict[str, Any]:
    payload: dict[str, Any] = {"studies": result.studies}
    if result.next_page_token is not None:
        payload["nextPageToken"] = result.next_page_token
    if result.total_count is not None:
        payload["totalCount"] = result.total_count
    return payload


def build_meta(spec: FixtureSpec, captured_at: str) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "horizon": spec.horizon_label,
        "fixture": f"{spec.name}.json",
        "captured_at": captured_at,
        "endpoint": "/studies",
        "source_query": spec.source_query,
        "request_params": spec.params.to_query_params(),
    }
    if spec.arm_label is not None:
        meta["arm_label"] = spec.arm_label
    if spec.comparison_group is not None:
        meta["comparison_group"] = spec.comparison_group
    return meta


def write_fixture(
    output_dir: Path,
    spec: FixtureSpec,
    payload: dict[str, Any],
    captured_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = output_dir / f"{spec.name}.json"
    meta_path = output_dir / f"{spec.name}.meta.json"

    with fixture_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(build_meta(spec, captured_at), handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Wrote {fixture_path}")


def capture_fixture(
    client: CtgovClient,
    output_dir: Path,
    spec: FixtureSpec,
    dry_run: bool,
) -> None:
    if dry_run:
        print(f"[dry-run] would capture {spec.name} -> {output_dir / spec.name}.json")
        return

    result = client.search_studies(spec.params)
    write_fixture(
        output_dir=output_dir,
        spec=spec,
        payload=search_result_payload(result),
        captured_at=utc_iso(),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture trimmed horizon API fixtures for tests.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for fixture JSON files (default: tests/fixtures/api/)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        help="Capture all horizon fixtures (default when no --fixture given)",
    )
    group.add_argument(
        "--fixture",
        choices=FIXTURE_NAMES,
        help="Capture a single fixture by name",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned captures without calling the API",
    )
    return parser.parse_args(argv)


def resolve_specs(args: argparse.Namespace) -> list[FixtureSpec]:
    if args.fixture is not None:
        return [spec for spec in FIXTURE_SPECS if spec.name == args.fixture]
    return list(FIXTURE_SPECS)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    specs = resolve_specs(args)

    if not args.dry_run:
        try:
            settings = Settings()
            client = ctgov_client_from_settings(settings)
            patch_client_urllib_transport(client)
        except Exception as exc:
            print(f"Failed to load settings: {exc}", file=sys.stderr)
            return 1
    else:
        client = None  # type: ignore[assignment]

    try:
        for spec in specs:
            capture_fixture(client, args.output_dir, spec, args.dry_run)
    except CtgovRateLimitError as exc:
        print(
            f"Rate limited (HTTP {exc.status_code}). Wait and retry.\n{exc.body[:500]}",
            file=sys.stderr,
        )
        return 1
    except CtgovApiError as exc:
        print(
            f"API error (HTTP {exc.status_code}): {exc.body[:500]}",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print("Dry run complete; no files written.")
    else:
        print(f"Capture complete. Files written under {args.output_dir}/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
