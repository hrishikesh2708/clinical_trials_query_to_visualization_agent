# Horizon matrix — query coverage and canonical fields

Stage 4 specification: which query classes the project commits to, which API JSON fields power each horizon, allowed/forbidden visualization types, and product rules for aggregation. This document is the single source of truth for Stage 6 mappers and Stage 8 query planning.

**Inputs:** [`docs/api/field_observations.md`](api/field_observations.md) (observed paths §1–7, semantics §8), [`app/domain/visualization.py`](../app/domain/visualization.py) (`VisualizationType`), [`app/core/schemas/visualization.py`](../app/core/schemas/visualization.py) (encoding shapes).

---

## Overview and scope

The project supports **five query horizons**, each mapping to at least one visualization type through the same pipeline (no one-off hacks):

| Horizon | Purpose |
|---------|---------|
| `time_trend` | How trial counts change over time |
| `distribution` | How trials spread across categorical or numeric buckets |
| `comparison` | Side-by-side counts across two or more arms |
| `geographic` | Where trials run (country-level) |
| `network` | Relationships among sponsors, drugs, and conditions |

**LLM never generates trial data.** Horizons define what Python aggregates from ClinicalTrials.gov API JSON. Enum code → display label mapping (e.g. `PHASE3` → `"Phase 3"`) is deferred to Stage 6 mappers via `/studies/enums`.

**Enforcement:** `allowed_visualization_types(horizon)` in [`app/domain/horizons.py`](../app/domain/horizons.py) encodes the compatibility matrix below. Stage 6 `VizCompatibilityValidator` will reject incompatible pairings at runtime.

---

## Confirmed product decisions (from §8)

| Topic | Decision |
|-------|----------|
| Time-trend canonical date | `protocolSection.statusModule.startDateStruct.date` — study start (recruitment opens / first enrollment) |
| `ACTUAL` vs `ESTIMATED` on date structs | **Prefer ACTUAL:** use date when `startDateStruct.type == "ACTUAL"`; otherwise use date when `type == "ESTIMATED"`; skip study if no parseable date |
| Multi-phase trials | **Explode:** count trial once per entry in `designModule.phases[]` |
| Geographic country dedup | **One count per study per unique** `locations[].country` |
| Comparison API fetch | **Two searches:** one API call per comparison arm; mapper merges with `series` = arm label |
| `query.locn` vs `filter.geo` | **Text vs radius:** `query.locn` for named places (country, city, facility); `filter.geo` only when user specifies proximity/radius (`distance(lat,lon,dist)`) |

Alternative date fields (`studyFirstSubmitDate`, `studyFirstPostDateStruct.date`) are documented in field observations but **not** used unless the user explicitly asks for registry submission or first-posted timelines (see [Out of scope](#out-of-scope-queries)).

---

## Per-horizon specifications

### 1. Time trend (`time_trend`)

**Allowed visualization:** `time_series` only.

**Example queries:**
- "Trials per year for pembrolizumab since 2015"
- "How many breast cancer trials started each year?"

**Canonical JSON paths:**

| Path | Use |
|------|-----|
| `studies[].protocolSection.statusModule.startDateStruct.date` | Bucket key (year/month/quarter/day) |
| `studies[].protocolSection.statusModule.startDateStruct.type` | `ACTUAL` / `ESTIMATED` inclusion rule |
| `studies[].protocolSection.identificationModule.nctId` | Citations, dedup key |

**Search params (`StudiesSearchParams`):**

| Param | When |
|-------|------|
| `query.intr` | Intervention-focused query (e.g. pembrolizumab) |
| `query.cond` | Condition-focused query (e.g. breast cancer) |
| `filter.advanced` | Date floor, e.g. `AREA[StartDate]2015` for "since 2015" |
| `count_total` | `true` on first page for total cohort size |

**`fields` projection (minimize payload):** `NCTId`, `StartDateStruct`

**Aggregation rules:**
1. Resolve start date per study using prefer-ACTUAL rule (see table above).
2. Skip studies with missing or unparseable `startDateStruct.date`.
3. Bucket by calendar year (default granularity); `TimeGranularity` from domain may refine to month/quarter/day in Stage 6.
4. Count one per study per time bucket (no explode).
5. Citations: `nctId` + excerpt from start date field (e.g. `"Study start date: 2018-03-15 (ACTUAL)."`).

**Citation excerpt sources:** `startDateStruct.date`, `startDateStruct.type`.

---

### 2. Distribution (`distribution`)

**Allowed visualizations:** `bar_chart`, `histogram`.

**Example queries:**
- "Breast cancer trials by phase"
- "Pembrolizumab trials by overall status"
- "Distribution of enrollment sizes for phase 3 oncology trials"

**Canonical JSON paths:**

| Path | Use |
|------|-----|
| `studies[].protocolSection.designModule.phases[]` | Primary categorical bucket (phase codes: `PHASE1`, `PHASE2`, …) |
| `studies[].protocolSection.statusModule.overallStatus` | Alt bucket: trial status (`RECRUITING`, `COMPLETED`, …) |
| `studies[].protocolSection.armsInterventionsModule.interventions[].type` | Alt bucket: intervention type |
| `studies[].protocolSection.designModule.enrollmentInfo.count` | Histogram bucket (numeric) |
| `studies[].protocolSection.identificationModule.nctId` | Citations |

**Search params:**

| Param | When |
|-------|------|
| `query.cond` | Condition cohort |
| `query.intr` | Intervention cohort |
| `filter.advanced` | Phase/status pre-filter, e.g. `AREA[Phase]PHASE3` |
| `filter.overall_status` | Status pre-filter |

**`fields` projection:**

| Bucket dimension | `fields` pieces |
|------------------|-----------------|
| Phase (default) | `NCTId`, `Phase` |
| Status | `NCTId`, `OverallStatus` |
| Intervention type | `NCTId`, `InterventionType` |
| Enrollment histogram | `NCTId`, `EnrollmentCount` |

**Aggregation rules:**
1. **Phase (default):** explode `phases[]` — each phase code gets one count contribution from the trial.
2. Trials with empty `phases[]` → bucket `NA` or omit (Stage 6 chooses; document as `"unknown"` bucket if present).
3. **Bar chart:** one row per category (`x` = bucket label, `y` = count).
4. **Histogram:** bin `enrollmentInfo.count` numerically; bin edges defined in Stage 6 mapper (e.g. fixed-width or quantile); skip studies with missing enrollment.
5. Citations per bucket row from the canonical field used.

**Citation excerpt sources:** phase array, `overallStatus`, `interventions[].type`, `enrollmentInfo.count`.

---

### 3. Comparison (`comparison`)

**Allowed visualizations:** `grouped_bar_chart` (primary), `bar_chart`.

**Example queries:**
- "Pembrolizumab vs nivolumab trials by phase"
- "Breast cancer vs lung cancer trial counts"
- "Industry vs academic sponsor trials for diabetes"

**Canonical JSON paths:** Same as distribution, plus:

| Path | Use |
|------|-----|
| `studies[].protocolSection.armsInterventionsModule.interventions[].name` | Arm labeling for intervention comparisons |
| `studies[].protocolSection.sponsorCollaboratorsModule.leadSponsor.name` | Arm labeling for sponsor comparisons |
| `studies[].protocolSection.sponsorCollaboratorsModule.leadSponsor.class` | Sponsor category (`INDUSTRY`, etc.) |
| `studies[].protocolSection.conditionsModule.conditions[]` | Arm labeling for condition comparisons |

**Search params — two-search strategy:**

| Comparison type | API calls |
|-----------------|-----------|
| Drug A vs drug B | `query.intr=A` and `query.intr=B` (separate searches) |
| Condition A vs B | `query.cond=A` and `query.cond=B` |
| Sponsor categories | One search per category filter or post-mapper split by `leadSponsor.class` |

Mapper tags each result set with `series` = arm label (query term or intervention name). **Grouped bar chart** when a second dimension exists (e.g. phase within each arm). **Bar chart** when comparing a single aggregate count per arm.

**`fields` projection:** `NCTId`, `Phase`, `InterventionName` (add `OverallStatus`, `LeadSponsorName`, `Condition` as needed for the comparison dimension).

**Aggregation rules:**
1. Run independent searches per arm; respect `pagination_cap` per arm.
2. Apply same distribution rules (explode phases, etc.) within each arm.
3. Merge into `grouped_bar_chart` encoding: `x` = bucket, `y` = count, `series` = arm label.
4. Citations retain arm context in excerpt.

---

### 4. Geographic (`geographic`)

**Allowed visualization:** `bar_chart` only.

**Example queries:**
- "Countries running pembrolizumab trials"
- "Where are phase 3 breast cancer trials located?"

**Canonical JSON paths:**

| Path | Use |
|------|-----|
| `studies[].protocolSection.contactsLocationsModule.locations[].country` | Country bucket |
| `studies[].protocolSection.identificationModule.nctId` | Citations, dedup key |

**Search params:**

| Param | When |
|-------|------|
| `query.intr` / `query.cond` | Define trial cohort |
| `query.locn` | User names a place — text search over city/state/country/facility/zip (e.g. "Germany", "Boston") |
| `filter.geo` | User specifies radius — `distance(lat,lon,dist)` (e.g. "within 50mi of Boston") |
| `filter.advanced` | Phase/status filters on cohort |

**Query planner rule (Stage 8):** Use `query.locn` for named geographic terms. Use `filter.geo` only when the user intent is proximity/radius with inferable or provided coordinates.

**`fields` projection:** `NCTId`, `LocationCountry` (or `ContactsLocationsModule` branch if leaf projection is insufficient for nested `locations[]`).

**Aggregation rules:**
1. For each study, collect unique `locations[].country` values (non-empty strings).
2. **Dedup:** increment each country's count **once per study** even if the study has many sites in that country.
3. Studies with no locations or no country → omit or `"Unknown"` bucket (Stage 6; prefer omit from chart).
4. Bar chart: `x` = country, `y` = trial count.
5. Citations: `nctId` + country from a representative location row.

**Citation excerpt sources:** `locations[].country`, optionally `locations[].city` for context.

---

### 5. Network (`network`)

**Allowed visualization:** `network_graph` only.

**Example queries:**
- "Pembrolizumab sponsor–drug–condition network"
- "Which sponsors study which drugs for melanoma?"

**Canonical JSON paths:**

| Path | Use |
|------|-----|
| `studies[].protocolSection.armsInterventionsModule.interventions[].name` | Drug nodes |
| `studies[].protocolSection.sponsorCollaboratorsModule.leadSponsor.name` | Sponsor nodes |
| `studies[].protocolSection.conditionsModule.conditions[]` | Condition nodes |
| `studies[].protocolSection.identificationModule.nctId` | Edge citations |
| `studies[].derivedSection.interventionBrowseModule.meshes[]` | Optional MeSH enrichment for drugs |
| `studies[].derivedSection.conditionBrowseModule.meshes[]` | Optional MeSH enrichment for conditions |

**Search params:** `query.intr` or `query.cond` to scope cohort; optional `filter.advanced` for phase/status.

**`fields` projection:** `NCTId`, `InterventionName`, `LeadSponsorName`, `Condition`, `DerivedSection` (or targeted derived leaves if API supports them).

**Node kinds (typed `kind` on `NetworkNode`):**

| Kind | Source field |
|------|--------------|
| `sponsor` | `leadSponsor.name` |
| `drug` | `interventions[].name` |
| `condition` | `conditions[]` |

**Edge rules (co-occurrence within same trial):**

| Edge | Source → target |
|------|-----------------|
| `sponsor↔drug` | `leadSponsor.name` ↔ each `interventions[].name` |
| `drug↔condition` | each `interventions[].name` ↔ each `conditions[]` |
| `drug↔drug` | each pair of distinct `interventions[].name` in same trial |

MeSH nodes from `derivedSection` are **optional enrichment** — MVP edges use protocol-section names only. Edge `label` may be `studied_in`, `sponsored_by`, `co_intervention`, etc. (Stage 6).

**Aggregation rules:**
1. One graph per query cohort (single search).
2. Deduplicate nodes by normalized id (lowercase name slug).
3. Edge weight = number of trials where both endpoints co-occur (Stage 6 may expose as edge label or metadata).
4. Citations on nodes and edges from contributing `nctId` excerpts.

---

## Compatibility matrix

| Horizon | Allowed | Forbidden |
|---------|---------|-----------|
| `time_trend` | `time_series` | `bar_chart`, `grouped_bar_chart`, `histogram`, `scatter_plot`, `network_graph` |
| `distribution` | `bar_chart`, `histogram` | `time_series`, `grouped_bar_chart`, `scatter_plot`, `network_graph` |
| `comparison` | `grouped_bar_chart`, `bar_chart` | `time_series`, `histogram`, `scatter_plot`, `network_graph` |
| `geographic` | `bar_chart` | `time_series`, `grouped_bar_chart`, `histogram`, `scatter_plot`, `network_graph` |
| `network` | `network_graph` | `time_series`, `bar_chart`, `grouped_bar_chart`, `histogram`, `scatter_plot` |

`scatter_plot` is not allowed on **any** horizon in this assignment.

Encoded in code:

```python
from app.domain.horizons import Horizon, allowed_visualization_types, is_visualization_compatible
```

---

## Cross-cutting rules

### Pagination

- Collect studies via `iter_search_studies` up to `pagination_cap` (settings default: 1000).
- Comparison horizon: cap applies **per arm** (two searches × cap worst case — Stage 8 may optimize).
- Always set `count_total=true` on the first page when total cohort size is needed for UI or validation.

### Empty results

- Return a **valid visualization shell** with empty data:
  - Tabular types: `data: []`
  - `network_graph`: `data: { "nodes": [], "edges": [] }`
- Do not fabricate placeholder trials or counts.

### Citations

- Every aggregated row, node, or edge may include `citations: [{ nct_id, excerpt }]`.
- Excerpt must quote or paraphrase a value from the canonical JSON path for that horizon.
- LLM does not invent excerpts; mappers extract from API JSON.
- Implementation: [`app/services/citation_engine.py`](../app/services/citation_engine.py).

**Per-datum cap:** `MAX_CITATIONS_PER_DATUM = 5` in the citation engine. Each bucket row, network node, or edge includes up to five representative trials (sorted by `nct_id`). This balances API response payload size against traceability — users can verify counts against real `nct_id` values without serializing every contributing study.

**Substring invariant:** `_excerpt_from_study_json()` requires each excerpt to appear verbatim in the serialized study JSON. Mappers cannot invent citation text.

**Bucket-aware excerpts:** The cited field must match the visualization dimension for that datum:
- Geographic: `locations[].country` matching the row's country bucket
- Distribution / comparison (phase): phase code matching the row's phase label
- Network nodes: sponsor name, intervention name, or condition string matching the node label
- Network edges: sponsor for `sponsored_by`; target condition for `studied_in`; source intervention for `co_intervention`
- Time trend: `startDateStruct.date`
- Enrollment histogram: `enrollmentInfo.count`

### Enum display labels

- API returns codes (`PHASE3`, `RECRUITING`). Human labels come from `/studies/enums` in Stage 6 — not defined here.

### Sort and relevance

- Default search sort is API relevance. Horizon mappers re-sort aggregated output (e.g. bar chart by count descending).

---

## Out-of-scope queries

Examples the project **does not** support in Stages 4–9 (reject or clarify in agent):

| Example | Reason |
|---------|--------|
| "Survival curves for pembrolizumab" | No results/outcomes horizon; requires `ResultsSection` |
| "Scatter plot of enrollment vs duration" | `scatter_plot` not assigned to any horizon |
| "Trials per year by first submission date" | Uses `studyFirstSubmitDate` — only if user explicitly requests submission timeline |
| "Trials per year by first posted date" | Uses `studyFirstPostDateStruct` — registry appearance, not clinical start |
| "Site-level counts without dedup" | Violates geographic dedup rule |
| "Patient-level demographics" | No individual-patient data in API |
| "Trial A vs Trial B efficacy" | Not a count/comparison horizon; needs results data |
| "All collaborators network" | MVP uses `leadSponsor` only; `collaborators[]` deferred |
| "Map with lat/lon pins" | Geographic horizon is country bar chart only, not choropleth/map viz |

---

## References

- Observed JSON paths: [`docs/api/field_observations.md`](api/field_observations.md)
- Search params: [`docs/api/studies.md`](api/studies.md), [`docs/api/search-areas.md`](api/search-areas.md)
- Field tree / `fields` pieces: [`docs/api/metadata.md`](api/metadata.md)
- Visualization types: [`app/domain/visualization.py`](../app/domain/visualization.py)
