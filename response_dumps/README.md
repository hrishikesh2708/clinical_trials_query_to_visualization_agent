# Response dumps (local only)

This directory holds **full raw API responses** captured from ClinicalTrials.gov for local exploration. Files here are **gitignored** and must never be committed.

## Purpose

Inspect real JSON shapes before horizon-matrix decisions (Stage 4) and trimmed test fixtures (Stage 5). This is exploratory tooling, not CI input.

## How to run

From the project root:

```bash
uv run python scripts/capture_raw_dumps.py
```

### Options

| Flag | Description |
|------|-------------|
| `--output-dir PATH` | Output directory (default: `response_dumps/`) |
| `--scenarios {studies,study,enums,metadata,search_areas,all}` | Subset of endpoint families (default: `all`) |
| `--dry-run` | Print planned captures without HTTP |

## Prerequisites

- Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (required by `Settings`, even though capture does not use it).
- Network access to `https://clinicaltrials.gov/api/v2`.

**Note:** The capture script patches `CtgovClient` to use `urllib` for HTTP because `httpx` receives HTTP 403 from clinicaltrials.gov in this environment. All endpoint calls still go through the existing client methods and models.

## What gets captured

| File prefix | Endpoint | Scenario |
|-------------|----------|----------|
| `studies_pembrolizumab_*` | `GET /studies` | Intervention search (`query.intr=Pembrolizumab`) |
| `studies_breast_cancer_*` | `GET /studies` | Condition search (`query.cond=breast cancer`) |
| `studies_obscure_*` | `GET /studies` | Near-empty result |
| `studies_pembrolizumab_page2_*` | `GET /studies` | Second page (`pageSize=5`) when `nextPageToken` exists |
| `study_NCT…_*` | `GET /studies/{nctId}` | Up to 3 NCT IDs from pembrolizumab search |
| `enums_*` | `GET /studies/enums` | Full enum payload |
| `metadata_*` | `GET /studies/metadata` | Field definitions |
| `search_areas_*` | `GET /studies/search-areas` | Search area definitions |

## File naming

Each capture writes two files sharing a UTC timestamp:

```
studies_pembrolizumab_20250629T143022.json
studies_pembrolizumab_20250629T143022.meta.json
```

- **`.json`** — pretty-printed response body
- **`.meta.json`** — sidecar with `captured_at`, `endpoint`, `scenario`, and `request_params`

Timestamp format: `YYYYMMDDTHHMMSS` (UTC).

## Idempotency

Each run creates **new timestamped files**. Re-running does not overwrite prior captures; older dumps remain for comparison.

## Next steps

- Review dumps and note field paths in [`docs/api/field_observations.md`](../docs/api/field_observations.md).
- Stage 5 will add trimmed, committed fixtures under `tests/fixtures/` for pytest.
