# Test fixtures

Committed, trimmed ClinicalTrials.gov API snapshots for offline mapper tests (Stage 6) and agent fragment tests (Stage 8).

## Layout

| Path | Purpose |
|------|---------|
| `api/*.json` | Trimmed `GET /studies` response payloads |
| `api/*.meta.json` | Capture metadata (horizon, request params, source query) |

**Not here (other stages):**

- `response_dumps/` — full exploratory captures (Stage 3, gitignored)
- `expected_viz/` — mapper golden outputs (Stage 6)

## Fixture inventory

| Fixture | Horizon | Source query |
|---------|---------|--------------|
| `time_trend_pembrolizumab.json` | `time_trend` | Trials per year for pembrolizumab since 2015 |
| `distribution_breast_cancer_phase.json` | `distribution` | Breast cancer trials by phase |
| `comparison_pembrolizumab_arm.json` | `comparison` | Pembrolizumab vs nivolumab — arm 1 |
| `comparison_nivolumab_arm.json` | `comparison` | Pembrolizumab vs nivolumab — arm 2 |
| `geographic_pembrolizumab_countries.json` | `geographic` | Countries running pembrolizumab trials |
| `network_diabetes_sponsor_drug.json` | `network` | Sponsor–drug–condition network for diabetes |
| `studies_empty.json` | `any` (edge) | Near-empty search |
| `studies_single.json` | `any` (edge) | Single-study pagination smoke |

Each fixture uses `fields` projections from `horizon_spec().fields_pieces` in [`app/domain/horizons.py`](../../app/domain/horizons.py). Search params and example queries are defined in [`docs/horizon_matrix.md`](../../docs/horizon_matrix.md).

## How fixtures were captured

```bash
uv run python scripts/capture_horizon_fixtures.py --all
```

The script:

1. Builds `StudiesSearchParams` per horizon from `FIXTURE_SPECS` in [`scripts/capture_horizon_fixtures.py`](../../scripts/capture_horizon_fixtures.py).
2. Calls `GET /studies` with `page_size=15` (or `1` for `studies_single`) and horizon-specific `fields` to minimize payload.
3. Writes stable filenames under `tests/fixtures/api/` plus `.meta.json` sidecars.
4. Uses urllib transport (patched from Stage 3) when httpx is blocked by the API.

## Refreshing fixtures

Re-capture a single fixture:

```bash
uv run python scripts/capture_horizon_fixtures.py --fixture time_trend_pembrolizumab
```

Re-capture all:

```bash
uv run python scripts/capture_horizon_fixtures.py --all
```

Preview without API calls:

```bash
uv run python scripts/capture_horizon_fixtures.py --dry-run
```

After refresh, run `uv run pytest tests/test_horizon_fixtures.py` to confirm fixtures still load and match expected shape.

## Trimming rules

- Keep API response shape: `{ "studies": [...], "nextPageToken"?, "totalCount"? }`.
- Rely on the `fields` query param so each study object contains only branches needed for that horizon's `canonical_json_paths`.
- Preserve real `nctId` values and citation-critical fields (e.g. `startDateStruct.type`).
- Do not commit full/raw dumps from `response_dumps/`.
