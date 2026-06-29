# Agent design — orchestration framework and pipeline contracts

Stage 7 specification: framework choice, per-step input/output contracts, LLM vs Python boundaries, and Stage 8 implementation map. **No agent code in this stage** — implementation starts in Stage 8.

**Normative references:**

- [`app/core/schemas/request.py`](../app/core/schemas/request.py) — `VisualizeRequest`
- [`app/core/schemas/response.py`](../app/core/schemas/response.py) — `VisualizeResponse`
- [`app/services/transform/__init__.py`](../app/services/transform/__init__.py) — `transform_studies()`
- [`app/infrastructure/ctgov/client.py`](../app/infrastructure/ctgov/client.py) — `CtgovClient`
- [`docs/horizon_matrix.md`](horizon_matrix.md) — horizon rules and API param guidance

---

## Core design principle

**The LLM never generates trial counts, chart data rows, network nodes, or edges.** It infers intent, proposes API query text, selects a visualization type from the allowed set, and writes human-facing narrative (title, assumptions, interpretation). Python owns API calls, pagination, `transform_studies()`, citations, and validation.

`transform_studies()` already runs `validate_pre_transform` and `validate_post_transform` — the agent layer must **not** duplicate those checks; it calls `transform_studies()` and surfaces `VizValidationError` as structured errors (HTTP mapping in Stage 9).

---

## Framework choice

### Selected: OpenAI SDK (structured outputs)

The visualize pipeline is implemented as a **linear orchestrator** with four LLM calls and two pure-Python steps. The OpenAI Python SDK provides Pydantic-native structured parsing (`client.beta.chat.completions.parse` or equivalent) that aligns with existing schema patterns in this project.

**Why OpenAI SDK fits:**

| Factor | Fit |
|--------|-----|
| Pipeline shape | Six fixed steps; comparison adds a second search, not dynamic graph routing |
| Validation | Centralized in `transform_studies()` — no need for per-node graph gates |
| Dependencies | `OPENAI_API_KEY` already required in [`app/core/config.py`](../app/core/config.py); add `openai` package in Stage 8a only |
| Schema style | Pydantic models throughout — `VisualizeRequest`, `StudiesSearchParams`, `TransformContext` |
| LLM call count | Four calls: Intent (1), Query plan draft (2), Viz selector (4), Response narrative (6) |

### Rejected alternatives

| Framework | Reason rejected |
|-----------|-----------------|
| **LangGraph** | Best when branching, retries, checkpointing, and per-fragment debugging dominate. This pipeline has fixed step order, validation inside `transform_studies()`, and comparison handled as “run search twice.” LangGraph adds state-machine boilerplate and a second orchestration model for little gain at current scope. Revisit if conversational follow-ups or multi-turn replanning are added. |
| **LangChain** | Broad toolkit without a specific integration win for a single-provider, narrow pipeline. Extra abstraction and dependency surface. |

### Orchestrator flow

```mermaid
flowchart LR
  req[VisualizeRequest] --> s1[Step1_IntentParser_LLM]
  s1 --> intent[Intent]
  intent --> s2[Step2_QueryPlanner_LLM_plus_Python]
  s2 --> plan[APIQueryPlan]
  plan --> s3[Step3_APICaller_Python]
  s3 --> raw[RawStudies]
  raw --> s4[Step4_VizSelector_LLM]
  s4 --> vizType[VisualizationType]
  vizType --> s5[Step5_transform_studies_Python]
  s5 --> viz[Visualization]
  viz --> s6[Step6_ResponseBuilder_LLM_plus_Python]
  s6 --> resp[VisualizeResponse]
```

---

## LLM vs Python responsibility

| Concern | Owner |
|---------|-------|
| Natural-language intent → horizon, bucket, granularity, arm labels | **LLM** (Step 1) |
| Trial counts, nodes, edges, chart data rows | **Python** (`transform_studies` + mappers) |
| API query text (`query.intr`, `query.cond`, `filter.advanced`, etc.) | **LLM proposes** (Step 2) → **Python validates/normalizes** |
| `fields` projection, `page_size`, `count_total`, pagination cap | **Python** (Step 2 normalizer + Step 3) |
| Fetching studies | **Python** (`CtgovClient.iter_search_studies`, cap from `Settings.pagination_cap`) |
| Viz type from allowed set | **LLM** (Step 4, constrained) + **Python** re-check via `allowed_visualization_types()` |
| Citations | **Python** (citation engine in mappers) |
| `meta.filters`, `total_studies_fetched` | **Python** (Step 6) |
| Title, `assumptions`, `interpretation_notes` | **LLM** (Step 6) |
| Horizon/viz compatibility, empty data, citations present | **Python** (`VizValidationError` inside `transform_studies`) |

---

## Pipeline steps

| Step | Name | Owner | Input → Output |
|------|------|-------|----------------|
| 1 | Intent parser | LLM + Python gate | `VisualizeRequest` → `Intent` |
| 2 | Query planner | LLM + Python | `Intent` → `QueryPlanDraft` → `APIQueryPlan` |
| 3 | API caller | Python | `APIQueryPlan` → raw studies per search |
| 4 | Viz type selector | LLM + Python gate | `Intent` + `FetchPreview` → `VisualizationType` |
| 5 | Transform | Python | `TransformContext` → `Visualization` |
| 6 | Response builder | LLM + Python | viz + context → `VisualizeResponse` |

---

## Type contracts (Stage 8: `app/agent/types.py`)

### Step 1 — `Intent`

```python
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.horizons import Horizon
from app.domain.visualization import TimeGranularity, VisualizationType

BucketField = Literal["phase", "overall_status", "enrollment"]


class ResolvedFilters(BaseModel):
    """Echo of structured filters after merging request + LLM inference."""

    drug_name: str | None = None
    condition: str | None = None
    trial_phase: str | None = None
    sponsor: str | None = None
    country: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class Intent(BaseModel):
    horizon: Horizon
    filters: ResolvedFilters
    bucket_field: BucketField | None = None
    time_granularity: TimeGranularity = TimeGranularity.YEAR
    comparison_arm_labels: tuple[str, ...] = ()
    suggested_viz_type: VisualizationType | None = None
    assumptions: list[str] = Field(default_factory=list)
```

**Python post-validation (Step 1 exit gate):**

- `comparison` → `len(comparison_arm_labels) >= 2`
- `distribution` → default `bucket_field` to `"phase"` if unset
- `time_trend` → `bucket_field` must be `None`
- `geographic` / `network` → `bucket_field` must be `None`
- Merge `VisualizeRequest` filter fields: explicit request values win over LLM-inferred values

**Example — time trend**

```json
{
  "horizon": "time_trend",
  "filters": {
    "drug_name": "Pembrolizumab",
    "condition": null,
    "trial_phase": null,
    "sponsor": null,
    "country": null,
    "start_year": 2015,
    "end_year": null
  },
  "bucket_field": null,
  "time_granularity": "year",
  "comparison_arm_labels": [],
  "suggested_viz_type": "time_series",
  "assumptions": [
    "Using study start date; preferring ACTUAL over ESTIMATED per horizon_matrix."
  ]
}
```

**Example — comparison**

```json
{
  "horizon": "comparison",
  "filters": {
    "drug_name": null,
    "condition": null,
    "trial_phase": null,
    "sponsor": null,
    "country": null,
    "start_year": null,
    "end_year": null
  },
  "bucket_field": "phase",
  "time_granularity": "year",
  "comparison_arm_labels": ["Pembrolizumab", "Nivolumab"],
  "suggested_viz_type": "grouped_bar_chart",
  "assumptions": [
    "Comparing intervention cohorts via separate query.intr searches."
  ]
}
```

---

### Step 2 — `QueryPlanDraft` (LLM) → `APIQueryPlan` (Python)

Step 2 is **LLM-assisted**: the model proposes search-relevant parameters; Python validates, normalizes, and injects operational fields.

**LLM output** — search text only (no `fields`, `page_token`, or pagination settings):

```python
class SearchParamsDraft(BaseModel):
    query_cond: str | None = None
    query_term: str | None = None
    query_locn: str | None = None
    query_intr: str | None = None
    query_spons: str | None = None
    query_lead: str | None = None
    filter_overall_status: list[str] | None = None
    filter_geo: str | None = None
    filter_advanced: str | None = None


class PlannedSearchDraft(BaseModel):
    label: str | None = None
    params: SearchParamsDraft


class QueryPlanDraft(BaseModel):
    searches: list[PlannedSearchDraft]
    planning_notes: list[str] = Field(default_factory=list)
```

**Python-normalized output:**

```python
from app.domain.horizons import Horizon
from app.infrastructure.ctgov.models import StudiesSearchParams


class PlannedSearch(BaseModel):
    label: str | None = None
    params: StudiesSearchParams
    fields: list[str]


class APIQueryPlan(BaseModel):
    horizon: Horizon
    searches: list[PlannedSearch]
    normalization_notes: list[str] = Field(default_factory=list)
```

**Python normalizer responsibilities:**

1. Set `fields` from `horizon_spec(horizon).fields_pieces` **plus bucket extensions** per [`horizon_matrix.md`](horizon_matrix.md):
   - `overall_status` bucket → add `OverallStatus`
   - `enrollment` bucket → add `EnrollmentCount`
   - other horizons → use spec defaults
2. Set `count_total=True` on each search (first page).
3. Set `page_size=100` (or settings default).
4. Build `filter.advanced` for `start_year`, `end_year`, `trial_phase` when not already in draft (`StudiesSearchParams.with_phases`, `AREA[StartDate]YYYY`).
5. Comparison: one `PlannedSearch` per arm with `label=comparison_arm_labels[i]` and arm-appropriate `query.intr` / `query.cond` / `query.spons`.
6. Geographic: enforce `query.locn` vs `filter.geo` rule from horizon_matrix.
7. Validate draft → `StudiesSearchParams` via Pydantic; reject unknown phase codes against `CtgovEnums`.
8. Append `normalization_notes` when Python overrides the LLM (e.g. forced `fields`, injected date filter).

**Doc/code note:** [`HorizonSpec.fields_pieces`](../app/domain/horizons.py) for `distribution` lists only `NCTId`, `Phase`. The query planner must extend `fields` for `overall_status` / `enrollment` buckets — no mapper change required.

**Example — distribution (breast cancer by phase)**

```json
{
  "horizon": "distribution",
  "searches": [
    {
      "label": null,
      "params": {
        "format": "json",
        "query_cond": "breast cancer",
        "count_total": true,
        "page_size": 100,
        "fields": ["NCTId", "Phase"]
      },
      "fields": ["NCTId", "Phase"]
    }
  ],
  "normalization_notes": ["Set count_total=true and fields from horizon spec."]
}
```

**Example — comparison (two arms)**

```json
{
  "horizon": "comparison",
  "searches": [
    {
      "label": "Pembrolizumab",
      "params": {
        "query_intr": "Pembrolizumab",
        "count_total": true,
        "page_size": 100,
        "fields": ["NCTId", "Phase", "InterventionName"]
      },
      "fields": ["NCTId", "Phase", "InterventionName"]
    },
    {
      "label": "Nivolumab",
      "params": {
        "query_intr": "Nivolumab",
        "count_total": true,
        "page_size": 100,
        "fields": ["NCTId", "Phase", "InterventionName"]
      },
      "fields": ["NCTId", "Phase", "InterventionName"]
    }
  ],
  "normalization_notes": []
}
```

---

### Step 3 — API caller (no new persisted types)

**Input:** `APIQueryPlan`

**Output:** `list[list[dict]]` — one study list per `PlannedSearch`, fetched via `CtgovClient.iter_search_studies(params)` respecting `Settings.pagination_cap`.

**Behavior:**

- Run searches sequentially (or in parallel if added later; Stage 8 default is sequential).
- Capture `total_count` from the first page of each search for `FetchPreview`.
- Fail with `empty_api_results` if any required search returns zero studies (all horizons require data today).

---

### Step 4 — `FetchPreview` and viz selection

**Python-built preview (Step 3 → Step 4):**

```python
class SearchPreview(BaseModel):
    label: str | None
    studies_fetched: int
    total_count: int | None


class FetchPreview(BaseModel):
    searches: list[SearchPreview]
    allowed_viz_types: list[VisualizationType]


class VizSelection(BaseModel):
    viz_type: VisualizationType
```

**LLM input:** `Intent` + `FetchPreview`

**LLM output:** `VizSelection` — `viz_type` must be in `allowed_viz_types`.

**Python gate:** Re-check via `allowed_visualization_types(intent.horizon)`. If LLM output is invalid, retry once with narrowed enum; if still invalid, fall back to sole allowed option or `suggested_viz_type` when compatible; else fail `incompatible_horizon_viz`.

**Distribution heuristics for Step 4:**

- `enrollment` bucket → prefer `histogram`
- categorical bucket → prefer `bar_chart`
- comparison with second dimension (phase) → prefer `grouped_bar_chart`

---

### Step 5 — `TransformContext` wiring

**Non-comparison:**

```python
TransformContext(
    horizon=intent.horizon,
    viz_type=selected_viz_type,
    studies=fetched_studies,
    bucket_field=intent.bucket_field or "phase",
    time_granularity=intent.time_granularity,
    enums=ctgov_enums_loader.load(),
)
```

**Comparison:**

```python
TransformContext(
    horizon=Horizon.COMPARISON,
    viz_type=selected_viz_type,
    comparison_arms=tuple(
        ComparisonArm(label=search.label, studies=arm_studies)
        for search, arm_studies in zip(plan.searches, per_arm_studies)
        if search.label is not None
    ),
    bucket_field="phase",
    enums=ctgov_enums_loader.load(),
)
```

Call `transform_studies(context)` — do not wrap or duplicate validation.

---

### Step 6 — `ResponseNarrative` and `VisualizeResponse`

**LLM output:**

```python
class ResponseNarrative(BaseModel):
    title: str
    interpretation_notes: str | None = None
    additional_assumptions: list[str] = Field(default_factory=list)
```

**Python assembles `VisualizeResponse`:**

```python
VisualizeResponse(
    visualization=viz,
    meta=ResponseMeta(
        filters=AppliedFilters(**intent.filters.model_dump()),
        assumptions=intent.assumptions + narrative.additional_assumptions,
        time_granularity=intent.time_granularity
        if intent.horizon is Horizon.TIME_TREND
        else None,
        total_studies_fetched=sum(len(s) for s in per_search_studies),
        interpretation_notes=narrative.interpretation_notes,
    ),
)
```

`Visualization` has no `title` field today. Stage 8e adds `title: str` to `ResponseMeta` (schema change) and sets it from `narrative.title`. Until then, the LLM title can be prepended to `interpretation_notes` during development only.

---

## Prompt surfaces (Stage 8)

| Step | Prompt? | System prompt content |
|------|---------|----------------------|
| 1 Intent | Yes | Five horizons, filter echo rules, `BucketField` / `TimeGranularity` enums, comparison arm extraction |
| 2 Query plan | Yes | ctgov param cheat sheet from horizon_matrix; output `QueryPlanDraft` only; one search per comparison arm |
| 3 API | No | — |
| 4 Viz select | Yes | Allowed viz types from preview; bucket/heuristic hints; output `VizSelection` |
| 5 Transform | No | — |
| 6 Response | Partial | Summarize viz encoding and cohort; no invented counts; output `ResponseNarrative` |

Prompt files (Stage 8a stubs): `app/agent/prompts/intent.md`, `query_plan.md`, `viz_select.md`, `response.md`.

---

## Error handling

| Condition | Code | Behavior |
|-----------|------|----------|
| `VizValidationError` from `transform_studies` | (from exception) | Propagate `code` + `message`; Stage 9 maps to HTTP 422 |
| Zero studies from API | `empty_api_results` | Fail before transform |
| LLM picks incompatible viz | `incompatible_horizon_viz` | Retry once in Step 4; then fail |
| LLM draft params fail Pydantic | `invalid_query_plan` | Retry Step 2 once with error context; then fail |
| Unknown phase in filter | `invalid_query_plan` | Fail in Step 2 normalizer |
| `CtgovRateLimitError` | — | Propagate; no LLM retry |
| `CtgovApiError` | — | Propagate; no LLM retry |
| OpenAI API errors | `llm_error` | Retry once per step (Stage 8); then fail |

The agent layer does **not** catch and swallow `VizValidationError` — it surfaces the existing `code` and `message` from [`app/validation/viz_compatibility.py`](../app/validation/viz_compatibility.py).

---

## Stage 8 fragment map

| Fragment | Scope | Pipeline steps |
|----------|-------|----------------|
| **8a** | Add `openai` to `pyproject.toml`; `app/agent/types.py`; `VisualizePipeline` orchestrator shell; prompt file stubs | scaffolding |
| **8b** | Step 1 Intent parser (LLM + Python validation) | Step 1 |
| **8c** | Step 2 Query planner (LLM draft + Python normalizer) | Step 2 |
| **8d** | Step 3 API caller + Step 4 Viz selector + `FetchPreview` builder | Steps 3–4 |
| **8e** | Step 5 transform wiring + Step 6 Response builder + end-to-end pipeline test with fixtures | Steps 5–6 |

**Stage 9 (out of scope):** `app/api/v1/visualize.py` HTTP handler wiring `VisualizePipeline` to `POST /v1/visualize`.

---

## Dependencies

| Package | When | Purpose |
|---------|------|---------|
| `openai` | Stage 8a | Chat completions with Pydantic structured outputs |

No new dependencies in Stage 7. Existing runtime deps (`fastapi`, `httpx`, `pydantic-settings`, `uvicorn`) are unchanged.

**Configuration (existing):**

- `OPENAI_API_KEY` — required in [`app/core/config.py`](../app/core/config.py)
- `pagination_cap` — caps studies fetched per search in Step 3
- `ctgov_base_url`, `http_timeout` — `CtgovClient` settings

---

## Exit criteria (Stage 7)

- [x] Framework choice documented with rationale and rejected alternatives
- [x] `Intent`, `QueryPlanDraft`, `APIQueryPlan`, `FetchPreview` shapes specified with JSON examples
- [x] LLM vs Python responsibility table
- [x] Stage 8a–8e fragment map aligned to pipeline steps
- [x] No `app/agent/` code or `pyproject.toml` changes in this stage

**Next:** Review and commit with message `docs: agent framework choice and pipeline step contracts`, then begin Stage 8a.
