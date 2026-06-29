"""Capture raw ClinicalTrials.gov API responses for local exploration.

Writes timestamped JSON dumps and .meta.json sidecars under response_dumps/.
Dumps are gitignored and must not be committed.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from typing import Any

from app.core.config import Settings
from app.infrastructure.ctgov.client import CtgovClient, ctgov_client_from_settings
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.metadata import MetadataParams
from app.infrastructure.ctgov.models import StudiesSearchParams, StudiesSearchResult

SCENARIO_CHOICES = ("studies", "study", "enums", "metadata", "search_areas", "all")
DEFAULT_OUTPUT_DIR = Path("response_dumps")


def patch_client_urllib_transport(client: CtgovClient) -> None:
    """Use urllib for live capture when httpx is blocked (403 on clinicaltrials.gov)."""

    def urllib_get(path: str, params: dict[str, str]) -> SimpleNamespace:
        query = urllib.parse.urlencode(params)
        url = f"{client._base_url}{path}"
        if query:
            url = f"{url}?{query}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=client._timeout) as response:
                body = response.read().decode()
                status_code = response.status
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            status_code = exc.code
        return SimpleNamespace(
            status_code=status_code,
            text=body,
            json=lambda body=body: json.loads(body),
        )

    client._get = urllib_get  # type: ignore[method-assign]


@dataclass(frozen=True)
class CaptureMeta:
    captured_at: str
    endpoint: str
    scenario: str
    request_params: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "captured_at": self.captured_at,
            "endpoint": self.endpoint,
            "scenario": self.scenario,
            "request_params": self.request_params,
        }


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S")


def utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def search_result_payload(result: StudiesSearchResult) -> dict[str, Any]:
    payload: dict[str, Any] = {"studies": result.studies}
    if result.next_page_token is not None:
        payload["nextPageToken"] = result.next_page_token
    if result.total_count is not None:
        payload["totalCount"] = result.total_count
    return payload


def extract_nct_ids(studies: list[dict[str, Any]], limit: int = 3) -> list[str]:
    nct_ids: list[str] = []
    for study in studies:
        nct_id = (
            study.get("protocolSection", {})
            .get("identificationModule", {})
            .get("nctId")
        )
        if isinstance(nct_id, str) and nct_id:
            nct_ids.append(nct_id)
        if len(nct_ids) >= limit:
            break
    return nct_ids


def write_dump(
    output_dir: Path,
    prefix: str,
    scenario: str,
    endpoint: str,
    request_params: dict[str, str],
    payload: Any,
    timestamp: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    dump_path = output_dir / f"{prefix}_{timestamp}.json"
    meta_path = output_dir / f"{prefix}_{timestamp}.meta.json"

    with dump_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    meta = CaptureMeta(
        captured_at=utc_iso(),
        endpoint=endpoint,
        scenario=scenario,
        request_params=request_params,
    )
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(meta.to_dict(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Wrote {dump_path}")
    return dump_path


def capture_studies(
    client: CtgovClient,
    output_dir: Path,
    timestamp: str,
    dry_run: bool,
) -> list[str]:
    scenarios: list[tuple[str, StudiesSearchParams]] = [
        (
            "pembrolizumab",
            StudiesSearchParams(query_intr="Pembrolizumab", count_total=True),
        ),
        (
            "breast_cancer",
            StudiesSearchParams(query_cond="breast cancer", count_total=True),
        ),
        (
            "obscure",
            StudiesSearchParams(query_term="xyzzy_nonexistent_trial_term_12345"),
        ),
    ]

    nct_ids: list[str] = []

    for scenario, params in scenarios:
        prefix = f"studies_{scenario}"
        if dry_run:
            print(f"[dry-run] would capture {prefix} -> /studies")
            continue

        result = client.search_studies(params)
        write_dump(
            output_dir=output_dir,
            prefix=prefix,
            scenario=scenario,
            endpoint="/studies",
            request_params=params.to_query_params(),
            payload=search_result_payload(result),
            timestamp=timestamp,
        )
        if scenario == "pembrolizumab":
            nct_ids = extract_nct_ids(result.studies)

    page_params = StudiesSearchParams(
        query_intr="Pembrolizumab",
        count_total=True,
        page_size=5,
    )
    prefix = "studies_pembrolizumab_page2"
    if dry_run:
        print(f"[dry-run] would capture {prefix} -> /studies (page 2 if available)")
        return nct_ids

    first_page = client.search_studies(page_params)
    if first_page.next_page_token:
        page2_params = page_params.model_copy(
            update={"page_token": first_page.next_page_token}
        )
        result = client.search_studies(page2_params)
        write_dump(
            output_dir=output_dir,
            prefix=prefix,
            scenario="pembrolizumab_page2",
            endpoint="/studies",
            request_params=page2_params.to_query_params(),
            payload=search_result_payload(result),
            timestamp=timestamp,
        )
    else:
        print("Skipping studies_pembrolizumab_page2: no nextPageToken on first page")

    return nct_ids


def capture_studies_by_nct(
    client: CtgovClient,
    output_dir: Path,
    timestamp: str,
    nct_ids: list[str],
    dry_run: bool,
) -> None:
    for nct_id in nct_ids:
        prefix = f"study_{nct_id}"
        if dry_run:
            print(f"[dry-run] would capture {prefix} -> /studies/{nct_id}")
            continue

        try:
            payload = client.get_study(nct_id)
        except ValueError as exc:
            print(f"Warning: skipping {nct_id}: {exc}", file=sys.stderr)
            continue

        write_dump(
            output_dir=output_dir,
            prefix=prefix,
            scenario=nct_id,
            endpoint=f"/studies/{nct_id}",
            request_params={"format": "json", "markupFormat": "markdown"},
            payload=payload,
            timestamp=timestamp,
        )


def capture_enums(
    client: CtgovClient,
    output_dir: Path,
    timestamp: str,
    dry_run: bool,
) -> None:
    prefix = "enums"
    if dry_run:
        print(f"[dry-run] would capture {prefix} -> /studies/enums")
        return

    payload = client.fetch_enums()
    write_dump(
        output_dir=output_dir,
        prefix=prefix,
        scenario="enums",
        endpoint="/studies/enums",
        request_params={},
        payload=payload,
        timestamp=timestamp,
    )


def capture_metadata(
    client: CtgovClient,
    output_dir: Path,
    timestamp: str,
    dry_run: bool,
) -> None:
    params = MetadataParams()
    prefix = "metadata"
    if dry_run:
        print(f"[dry-run] would capture {prefix} -> /studies/metadata")
        return

    response = client._get("/studies/metadata", params.to_query_params())
    if response.status_code >= 400:
        raise CtgovApiError(response.status_code, response.text)
    payload = response.json()
    write_dump(
        output_dir=output_dir,
        prefix=prefix,
        scenario="metadata",
        endpoint="/studies/metadata",
        request_params=params.to_query_params(),
        payload=payload,
        timestamp=timestamp,
    )


def capture_search_areas(
    client: CtgovClient,
    output_dir: Path,
    timestamp: str,
    dry_run: bool,
) -> None:
    prefix = "search_areas"
    if dry_run:
        print(f"[dry-run] would capture {prefix} -> /studies/search-areas")
        return

    response = client._get("/studies/search-areas", {})
    if response.status_code >= 400:
        raise CtgovApiError(response.status_code, response.text)
    payload = response.json()
    write_dump(
        output_dir=output_dir,
        prefix=prefix,
        scenario="search_areas",
        endpoint="/studies/search-areas",
        request_params={},
        payload=payload,
        timestamp=timestamp,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture raw ClinicalTrials.gov API responses.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON dumps (default: response_dumps/)",
    )
    parser.add_argument(
        "--scenarios",
        choices=SCENARIO_CHOICES,
        default="all",
        help="Which endpoint families to capture (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned captures without calling the API",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = utc_timestamp()
    selected = args.scenarios
    run_all = selected == "all"

    try:
        settings = Settings()
        client = ctgov_client_from_settings(settings)
        if not args.dry_run:
            patch_client_urllib_transport(client)
    except Exception as exc:
        print(f"Failed to load settings: {exc}", file=sys.stderr)
        return 1

    nct_ids: list[str] = []

    try:
        if run_all or selected == "studies":
            nct_ids = capture_studies(
                client, args.output_dir, timestamp, args.dry_run
            )

        if run_all or selected == "study":
            if not nct_ids and not args.dry_run:
                print(
                    "Warning: no NCT IDs from pembrolizumab search; "
                    "run studies scenarios first or use --scenarios all",
                    file=sys.stderr,
                )
            capture_studies_by_nct(
                client, args.output_dir, timestamp, nct_ids, args.dry_run
            )

        if run_all or selected == "enums":
            capture_enums(client, args.output_dir, timestamp, args.dry_run)

        if run_all or selected == "metadata":
            capture_metadata(client, args.output_dir, timestamp, args.dry_run)

        if run_all or selected == "search_areas":
            capture_search_areas(client, args.output_dir, timestamp, args.dry_run)

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
