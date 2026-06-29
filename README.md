# ClinicalTrials.gov Query-to-Visualization Agent

FastAPI backend that accepts a natural-language query (plus optional structured filters), plans ClinicalTrials.gov API searches, aggregates trial data in Python, and returns a typed visualization with citations and narrative metadata.

The LLM handles intent, query planning, visualization selection, and human-facing narrative. Python owns API calls, pagination, aggregation, citations, and validation. See [docs/agent_design.md](docs/agent_design.md) for the full pipeline design.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key (required at runtime and for tests)
- Network access when calling the live ClinicalTrials.gov API

## Setup

```bash
git clone <repo-url>
cd ClinicalTrials
uv sync
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

## Configuration

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | Yes | — | OpenAI structured-output calls |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for agent LLM steps |
| `CTGOV_BASE_URL` | No | `https://clinicaltrials.gov/api/v2` | ClinicalTrials.gov API base |
| `HTTP_TIMEOUT` | No | `30.0` | HTTP client timeout (seconds) |
| `PAGINATION_CAP` | No | `1000` | Max studies fetched per search |

Settings are loaded from `.env` via [app/core/config.py](app/core/config.py). Do not commit `.env`.

**ClinicalTrials.gov HTTP client:** The API WAF blocks Python clients with httpx's TLS fingerprint (403 Forbidden). [`CtgovClient`](app/infrastructure/ctgov/client.py) uses stdlib `urllib` via [`app/infrastructure/ctgov/transport.py`](app/infrastructure/ctgov/transport.py) instead.

## Run the server

```bash
uv run uvicorn app.main:app --reload
```

- Health check: `GET http://127.0.0.1:8000/health`
- OpenAPI UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Main endpoint: `POST /api/v1/visualize`

## Optional Streamlit demo

A thin UI for interactive exploration lives in [`ui/`](ui/). It calls the running FastAPI backend over HTTP and renders charts from the response — it does not call OpenAI or ClinicalTrials.gov directly.

```bash
# Terminal 1 — backend
uv sync
uv run uvicorn app.main:app --reload

# Terminal 2 — UI
uv sync --group ui
uv run streamlit run ui/app.py
```

Open [http://localhost:8501](http://localhost:8501). The sidebar lists sample queries with **five network examples** at the top (README documents two network queries under [Sample queries](#sample-queries)). Optional `BACKEND_URL` in `.env` defaults to `http://127.0.0.1:8000`.

## API usage

Sample request (time trend — see [Example outputs](#example-outputs) for live curl + response):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Trials per year for pembrolizumab since 2015",
    "drug_name": "Pembrolizumab",
    "start_year": 2015
  }'
```

Live calls need a valid `OPENAI_API_KEY` and outbound network to OpenAI and ClinicalTrials.gov.

## Request / response schemas

Full schemas are available in the **OpenAPI UI at `/docs`**. Source models: [app/core/schemas/request.py](app/core/schemas/request.py), [app/core/schemas/response.py](app/core/schemas/response.py).

### VisualizeRequest

| Field | Type | Notes |
|-------|------|-------|
| `query` | string (required) | Natural-language question |
| `drug_name`, `condition`, `trial_phase`, `sponsor`, `country` | string \| null | Optional structured filters |
| `start_year`, `end_year` | int \| null | 1900–2100; `start_year <= end_year` when both set |

### VisualizeResponse

| Field | Contents |
|-------|----------|
| `visualization` | Discriminated by `type` (`time_series`, `bar_chart`, `grouped_bar_chart`, `histogram`, `network_graph`, …) with `encoding` + `data` rows including `citations` |
| `meta` | `title`, `source`, `filters`, `assumptions`, `time_granularity`, `units`, `total_studies_fetched`, `interpretation_notes` |

Each data row, node, or edge with a non-zero count includes up to **5 citations** (`nct_id` + `excerpt`). Details: [docs/horizon_matrix.md](docs/horizon_matrix.md).

## Architecture

Layered layout:

- **API** — [app/api/v1/visualize.py](app/api/v1/visualize.py): HTTP + error mapping
- **Agent** — [app/agent/pipeline.py](app/agent/pipeline.py): 6-step orchestrator (4 LLM + 2 Python)
- **Services** — transform mappers, citation engine, fetch
- **Infrastructure** — [app/infrastructure/ctgov/](app/infrastructure/ctgov/): API client
- **Domain / schemas** — horizons, visualization types, Pydantic contracts

Deep dive: [docs/agent_design.md](docs/agent_design.md).

## Supported query horizons and visualization types

| Horizon | Example query theme | Allowed viz types |
|---------|---------------------|-------------------|
| `time_trend` | Trials per year over time | `time_series` |
| `distribution` | Counts by phase, status, etc. | `bar_chart`, `histogram` |
| `comparison` | Side-by-side arms (e.g. drug A vs B) | `grouped_bar_chart`, `bar_chart` |
| `geographic` | Trials by country | `bar_chart` |
| `network` | Sponsor–drug–condition relationships | `network_graph` |

Full rules, JSON paths, and out-of-scope queries: [docs/horizon_matrix.md](docs/horizon_matrix.md).

## Citations

- Cap: `MAX_CITATIONS_PER_DATUM = 5` in [app/services/citation_engine.py](app/services/citation_engine.py)
- **Substring rule:** each excerpt must appear verbatim in the serialized study JSON — mappers cannot invent text
- Bucket-aware excerpts per horizon (documented in [docs/horizon_matrix.md](docs/horizon_matrix.md))

## Testing and linting

Tests expect a real `OPENAI_API_KEY` in `.env` (see [tests/conftest.py](tests/conftest.py)).

```bash
uv run pytest
uv run ruff check .
```

### Validation approach

| Layer | What is checked |
|-------|-----------------|
| Transform golden tests | Fixture studies → viz shape/counts vs `tests/fixtures/expected_viz/` |
| Citation tests | Every row has citations; excerpts are substrings of source JSON |
| Example outputs | [tests/test_examples_citations.py](tests/test_examples_citations.py) validates all `examples/*.json` |
| API tests | Mocked pipeline per horizon ([tests/api/test_visualize.py](tests/api/test_visualize.py)); error paths return 422 |
| Agent unit tests | Intent parser, query planner, normalizer, viz selector (mocked LLM) |
| Schema tests | Request/response/OpenAPI contract |

## Design decisions and tradeoffs

- **Layered architecture** — clear boundaries between HTTP, orchestration, domain transforms, and ct.gov client
- **OpenAI SDK over LangGraph/LangChain** — fixed 6-step linear pipeline; structured Pydantic outputs; fewer moving parts ([docs/agent_design.md](docs/agent_design.md))
- **LLM vs Python split** — LLM never generates counts, chart rows, or network edges; Python owns all trial data
- **Horizon matrix as SSOT** — compatibility and field projections centralized in [docs/horizon_matrix.md](docs/horizon_matrix.md) and [app/domain/horizons.py](app/domain/horizons.py)
- **Citation cap** — 5 per datum balances traceability vs response size
- **Fixture-backed examples** — reproducible submission outputs without live API dependency at generation time

## Limitations and future work

- **Pagination cap** (`PAGINATION_CAP`, default 1000) — large cohorts are truncated per search; comparison runs two searches
- **LLM variability** — intent, query, and viz selection may differ between runs; validation catches incompatible horizon/viz pairings
- **Unsupported viz** — `scatter_plot` not assigned to any horizon; no choropleth/map, survival curves, or results/outcomes analysis
- **Geographic scope** — country-level bar chart only; site-level dedup rules apply
- **Network MVP** — lead sponsor only; collaborators deferred
- **No conversational follow-ups** — single-shot query per request

See [Out-of-scope queries](docs/horizon_matrix.md#out-of-scope-queries) in the horizon matrix.

## AI tools and disclosure

| Tool | Role |
|------|------|
| **Cursor** | IDE pair-programming, scaffolding, test/debug assistance |
| **OpenAI API** | Runtime LLM for intent, query planning, viz selection, narrative |

**Human-designed:** horizon matrix, schema contracts, transform mappers, citation engine, pipeline orchestration, test strategy, API error mapping.

**AI-assisted / generated:** boilerplate, test cases, doc drafts, iterative implementation — reviewed and validated against fixtures and golden outputs.

## Example outputs

Live responses from `POST /api/v1/visualize` (running server, `OPENAI_API_KEY`, and outbound network). Full JSON files are in [`examples/live/`](examples/live/). Mocked fixture copies used by tests remain in [`examples/`](examples/).

Each block below is a **collapsible `<details>` section** (works on GitHub). The summary line shows visualization type and counts; expand for the curl command, a metadata table, and JSON (inlined when ≤8 KB, otherwise a file link plus a 40-line preview).

### Add or refresh an example

```bash
# 1. Capture response
curl ... | python3 -m json.tool > examples/live/my_example.json

# 2. Render markdown snippet
uv run python scripts/render_readme_example.py \
  --title "Short label" \
  --curl-file examples/live/curls/my_example.sh \
  --json examples/live/my_example.json
```

To regenerate the [sample queries](#sample-queries) section, edit [`examples/live/sample_queries/manifest.json`](examples/live/sample_queries/manifest.json) and run:

```bash
uv run python scripts/render_sample_queries_section.py
```

### One example per horizon
<details>
<summary><strong>Time trend — Pembrolizumab trials per year since 2015 — time_series, 13 data rows, 1000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Trials per year for pembrolizumab since 2015",
    "drug_name": "Pembrolizumab",
    "start_year": 2015
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | time_series |
| Title | Trials started per year since 2010 |
| Data | 13 data rows |
| Studies fetched | 1000 |
| Time granularity | year |
| Filters applied | drug_name=Pembrolizumab, start_year=2015 |

**Full response**

Saved to [`examples/live/time_trend_pembrolizumab.json`](examples/live/time_trend_pembrolizumab.json) (8,143 bytes).

<details>
<summary>Preview (first 40 lines)</summary>

```json
{
  "visualization": {
    "type": "time_series",
    "encoding": {
      "x": "year",
      "y": "count",
      "series": null
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT02260440",
            "excerpt": "2015-01"
          },
          {
            "nct_id": "NCT02268825",
            "excerpt": "2015-01-23"
          },
          {
            "nct_id": "NCT02298959",
            "excerpt": "2015-04-08"
          },
          {
            "nct_id": "NCT02301039",
            "excerpt": "2015-03"
          },
          {
            "nct_id": "NCT02305186",
            "excerpt": "2015-03"
          }
        ],
        "year": 2015,
        "count": 54
      },
      {
        "citations": [
          {
            "nct_id": "NCT02432963",
            "excerpt": "2016-06-14"
...
```

</details>

</details>


<details>
<summary><strong>Distribution — Breast cancer trials by phase — bar_chart, 7 data rows, 1000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How are breast cancer trials distributed across phases?"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | bar_chart |
| Title | Distribution of Clinical Trials by Phase |
| Data | 7 data rows |
| Studies fetched | 1000 |
| Time granularity | — |
| Filters applied | condition=breast cancer |

**Full response**

<details>
<summary>JSON (click to expand)</summary>

```json
{
  "visualization": {
    "type": "bar_chart",
    "encoding": {
      "x": "phase",
      "y": "count"
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT00002509",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00002680",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00003041",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00003042",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00003199",
            "excerpt": "PHASE2"
          }
        ],
        "phase": "Phase 2",
        "count": 299
      },
      {
        "citations": [
          {
            "nct_id": "NCT00066586",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00072501",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00126464",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00208871",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00293865",
            "excerpt": "NA"
          }
        ],
        "phase": "Not Applicable",
        "count": 275
      },
      {
        "citations": [
          {
            "nct_id": "NCT00002900",
            "excerpt": "NCT00002900"
          },
          {
            "nct_id": "NCT00003000",
            "excerpt": "NCT00003000"
          },
          {
            "nct_id": "NCT00161265",
            "excerpt": "NCT00161265"
          },
          {
            "nct_id": "NCT00210145",
            "excerpt": "NCT00210145"
          },
          {
            "nct_id": "NCT00291122",
            "excerpt": "NCT00291122"
          }
        ],
        "phase": "Unknown",
        "count": 217
      },
      {
        "citations": [
          {
            "nct_id": "NCT00002509",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00002616",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00003412",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00004207",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00005886",
            "excerpt": "PHASE1"
          }
        ],
        "phase": "Phase 1",
        "count": 143
      },
      {
        "citations": [
          {
            "nct_id": "NCT00002528",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00002564",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00003013",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00003577",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00003679",
            "excerpt": "PHASE3"
          }
        ],
        "phase": "Phase 3",
        "count": 103
      },
      {
        "citations": [
          {
            "nct_id": "NCT00087620",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT00160901",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT00754767",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT01049295",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT01156961",
            "excerpt": "PHASE4"
          }
        ],
        "phase": "Phase 4",
        "count": 25
      },
      {
        "citations": [
          {
            "nct_id": "NCT00640861",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03113019",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT04265872",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT04541108",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT04630210",
            "excerpt": "EARLY_PHASE1"
          }
        ],
        "phase": "Early Phase 1",
        "count": 8
      }
    ]
  },
  "meta": {
    "title": "Distribution of Clinical Trials by Phase",
    "source": "clinicaltrials.gov",
    "filters": {
      "drug_name": null,
      "condition": "breast cancer",
      "trial_phase": null,
      "sponsor": null,
      "country": null,
      "start_year": null,
      "end_year": null
    },
    "assumptions": [
      "The query focuses on the distribution of trials by phase, hence the bucket field is set to 'phase'.",
      "No specific drug, sponsor, or country is mentioned, so those filters remain null.",
      "The data does not specify any particular drug, sponsor, or country, which may affect the interpretation of the distribution."
    ],
    "time_granularity": null,
    "units": null,
    "total_studies_fetched": 1000,
    "interpretation_notes": "This bar chart illustrates the distribution of clinical trials categorized by their respective phases. A total of 1000 studies were fetched, with 7 distinct phases represented in the data."
  }
}
```

</details>

</details>


<details>
<summary><strong>Comparison — Pembrolizumab vs nivolumab by phase — grouped_bar_chart, 14 data rows, 2000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare phases for trials involving pembrolizumab vs nivolumab"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | grouped_bar_chart |
| Title | Comparison of Pembrolizumab and Nivolumab Trials by Phase |
| Data | 14 data rows |
| Studies fetched | 2000 |
| Time granularity | — |
| Filters applied | none |

**Full response**

Saved to [`examples/live/comparison_pembrolizumab_vs_nivolumab.json`](examples/live/comparison_pembrolizumab_vs_nivolumab.json) (9,449 bytes).

<details>
<summary>Preview (first 40 lines)</summary>

```json
{
  "visualization": {
    "type": "grouped_bar_chart",
    "encoding": {
      "x": "phase",
      "y": "count",
      "series": "series"
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT02652455",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03143270",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03311958",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03371992",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03463408",
            "excerpt": "EARLY_PHASE1"
          }
        ],
        "phase": "Early Phase 1",
        "series": "nivolumab",
        "count": 18
      },
      {
        "citations": [
          {
            "nct_id": "NCT03153410",
...
```

</details>

</details>


<details>
<summary><strong>Geographic — Recruiting lung cancer trials by country — bar_chart, 68 data rows, 1000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Recruiting lung cancer trials by country"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | bar_chart |
| Title | Lung cancer trials by country |
| Data | 68 data rows |
| Studies fetched | 1000 |
| Time granularity | — |
| Filters applied | condition=lung cancer |

**Full response**

Saved to [`examples/live/geographic_lung_cancer_recruiting.json`](examples/live/geographic_lung_cancer_recruiting.json) (34,190 bytes).

<details>
<summary>Preview (first 40 lines)</summary>

```json
{
  "visualization": {
    "type": "bar_chart",
    "encoding": {
      "x": "country",
      "y": "count"
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT00001465",
            "excerpt": "United States"
          },
          {
            "nct_id": "NCT00002506",
            "excerpt": "United States"
          },
          {
            "nct_id": "NCT00003881",
            "excerpt": "United States"
          },
          {
            "nct_id": "NCT00004011",
            "excerpt": "United States"
          },
          {
            "nct_id": "NCT00004160",
            "excerpt": "United States"
          }
        ],
        "country": "United States",
        "count": 397
      },
      {
        "citations": [
          {
            "nct_id": "NCT00686959",
            "excerpt": "China"
          },
...
```

</details>

</details>


<details>
<summary><strong>Network — Diabetes sponsor–drug network — network_graph, 2619 nodes, 5422 edges, 1000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show a network of sponsors and drugs for diabetes trials"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | network_graph |
| Title | Diabetes sponsor–drug–condition network |
| Data | 2619 nodes, 5422 edges |
| Studies fetched | 1000 |
| Time granularity | — |
| Filters applied | condition=diabetes |

**Full response**

Saved to [`examples/live/network_diabetes_sponsor_drug.json`](examples/live/network_diabetes_sponsor_drug.json) (2,494,403 bytes).

<details>
<summary>Preview (first 40 lines)</summary>

```json
{
  "visualization": {
    "type": "network_graph",
    "encoding": {
      "nodes": "nodes",
      "edges": "edges"
    },
    "data": {
      "nodes": [
        {
          "id": "steen-andersen",
          "label": "Steen Andersen",
          "citations": [
            {
              "nct_id": "NCT01454700",
              "excerpt": "Steen Andersen"
            }
          ]
        },
        {
          "id": "insulin-pump-therapy-csii-plus-continuous-glucose-monitoring-cgm",
          "label": "Insulin pump therapy (CSII) plus continuous glucose monitoring (CGM)",
          "citations": [
            {
              "nct_id": "NCT01454700",
              "excerpt": "Insulin pump therapy (CSII) plus continuous glucose monitoring (CGM)"
            }
          ]
        },
        {
          "id": "multiple-daily-insulin-injections-mdi",
          "label": "Multiple daily insulin injections (MDI)",
          "citations": [
            {
              "nct_id": "NCT01454700",
              "excerpt": "Multiple daily insulin injections (MDI)"
            }
          ]
        },
        {
...
```

</details>

</details>


## Submission package checklist

**Include in zip:**

- All source code (`app/`, `tests/`, `scripts/`, `docs/`, `examples/`, `pyproject.toml`, `.env.example`, etc.)
- Complete README
- 3–5 example JSON files in `examples/` (5 fixture files) plus live captures in `examples/live/`

**Exclude:**

- `.venv/`, `.env`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- `response_dumps/*.json` (gitignored; see [.gitignore](.gitignore))

**Optional zip command:**

```bash
zip -r clinicaltrials-agent.zip . \
  -x '.venv/*' -x '.env' -x 'response_dumps/*' \
  -x '__pycache__/*' -x '.pytest_cache/*' -x '.ruff_cache/*'
```



## Sample queries

Natural-language queries grouped by horizon.
Each block is collapsible on GitHub.
Entries with a captured response include a summary table
and JSON preview/link.

### Time trend

<details>
<summary><strong>Pembrolizumab trials over time (structured drug filter)</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How has the number of trials for this drug changed over time?",
    "drug_name": "Pembrolizumab"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Pembrolizumab trials per year since 2015</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How has the number of trials for Pembrolizumab changed per year since 2015"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Pembrolizumab trials per year from 2015 to 2018</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How has the number of trials for Pembrolizumab changed per year from 2015 to 2018"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Diabetes trials started each year</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many trials started each year for diabetes"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

### Distribution

<details>
<summary><strong>Breast cancer trials by phase — bar_chart, 7 data rows, 1000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How are breast cancer trials distributed across phases?"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | bar_chart |
| Title | Distribution of Clinical Trials by Phase |
| Data | 7 data rows |
| Studies fetched | 1000 |
| Time granularity | — |
| Filters applied | condition=breast cancer |

**Full response**

<details>
<summary>JSON (click to expand)</summary>

```json
{
  "visualization": {
    "type": "bar_chart",
    "encoding": {
      "x": "phase",
      "y": "count"
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT00002509",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00002680",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00003041",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00003042",
            "excerpt": "PHASE2"
          },
          {
            "nct_id": "NCT00003199",
            "excerpt": "PHASE2"
          }
        ],
        "phase": "Phase 2",
        "count": 299
      },
      {
        "citations": [
          {
            "nct_id": "NCT00066586",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00072501",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00126464",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00208871",
            "excerpt": "NA"
          },
          {
            "nct_id": "NCT00293865",
            "excerpt": "NA"
          }
        ],
        "phase": "Not Applicable",
        "count": 275
      },
      {
        "citations": [
          {
            "nct_id": "NCT00002900",
            "excerpt": "NCT00002900"
          },
          {
            "nct_id": "NCT00003000",
            "excerpt": "NCT00003000"
          },
          {
            "nct_id": "NCT00161265",
            "excerpt": "NCT00161265"
          },
          {
            "nct_id": "NCT00210145",
            "excerpt": "NCT00210145"
          },
          {
            "nct_id": "NCT00291122",
            "excerpt": "NCT00291122"
          }
        ],
        "phase": "Unknown",
        "count": 217
      },
      {
        "citations": [
          {
            "nct_id": "NCT00002509",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00002616",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00003412",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00004207",
            "excerpt": "PHASE1"
          },
          {
            "nct_id": "NCT00005886",
            "excerpt": "PHASE1"
          }
        ],
        "phase": "Phase 1",
        "count": 143
      },
      {
        "citations": [
          {
            "nct_id": "NCT00002528",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00002564",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00003013",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00003577",
            "excerpt": "PHASE3"
          },
          {
            "nct_id": "NCT00003679",
            "excerpt": "PHASE3"
          }
        ],
        "phase": "Phase 3",
        "count": 103
      },
      {
        "citations": [
          {
            "nct_id": "NCT00087620",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT00160901",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT00754767",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT01049295",
            "excerpt": "PHASE4"
          },
          {
            "nct_id": "NCT01156961",
            "excerpt": "PHASE4"
          }
        ],
        "phase": "Phase 4",
        "count": 25
      },
      {
        "citations": [
          {
            "nct_id": "NCT00640861",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03113019",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT04265872",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT04541108",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT04630210",
            "excerpt": "EARLY_PHASE1"
          }
        ],
        "phase": "Early Phase 1",
        "count": 8
      }
    ]
  },
  "meta": {
    "title": "Distribution of Clinical Trials by Phase",
    "source": "clinicaltrials.gov",
    "filters": {
      "drug_name": null,
      "condition": "breast cancer",
      "trial_phase": null,
      "sponsor": null,
      "country": null,
      "start_year": null,
      "end_year": null
    },
    "assumptions": [
      "The query focuses on the distribution of trials by phase, hence the bucket field is set to 'phase'.",
      "No specific drug, sponsor, or country is mentioned, so those filters remain null.",
      "The data does not specify any particular drug, sponsor, or country, which may affect the interpretation of the distribution."
    ],
    "time_granularity": null,
    "units": null,
    "total_studies_fetched": 1000,
    "interpretation_notes": "This bar chart illustrates the distribution of clinical trials categorized by their respective phases. A total of 1000 studies were fetched, with 7 distinct phases represented in the data."
  }
}
```

</details>

</details>

<details>
<summary><strong>Diabetes trials by intervention type</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the most common intervention types for diabetes trials?"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Pembrolizumab recruiting vs completed</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many pembrolizumab trials are recruiting vs completed?"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Alzheimer's trials by intervention type</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What intervention types are most common in Alzheimer'\''s trials?"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Diabetes trials by recruitment status</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the recruitment status breakdown for diabetes trials?"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

### Comparison

<details>
<summary><strong>Pembrolizumab vs nivolumab by phase — grouped_bar_chart, 14 data rows, 2000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare phases for trials involving pembrolizumab vs nivolumab"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | grouped_bar_chart |
| Title | Comparison of Pembrolizumab and Nivolumab Trials by Phase |
| Data | 14 data rows |
| Studies fetched | 2000 |
| Time granularity | — |
| Filters applied | none |

**Full response**

Saved to [`examples/live/comparison_pembrolizumab_vs_nivolumab.json`](examples/live/comparison_pembrolizumab_vs_nivolumab.json) (9,449 bytes).

<details>
<summary>Preview (first 40 lines)</summary>

```json
{
  "visualization": {
    "type": "grouped_bar_chart",
    "encoding": {
      "x": "phase",
      "y": "count",
      "series": "series"
    },
    "data": [
      {
        "citations": [
          {
            "nct_id": "NCT02652455",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03143270",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03311958",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03371992",
            "excerpt": "EARLY_PHASE1"
          },
          {
            "nct_id": "NCT03463408",
            "excerpt": "EARLY_PHASE1"
          }
        ],
        "phase": "Early Phase 1",
        "series": "nivolumab",
        "count": 18
      },
      {
        "citations": [
          {
            "nct_id": "NCT03153410",
...
```

</details>

</details>

<details>
<summary><strong>Metformin vs insulin by recruitment status</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do metformin and insulin trials compare by recruitment status?"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Breast cancer vs lung cancer by phase</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare breast cancer vs lung cancer trial counts by phase"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Breast vs lung cancer sponsor categories</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare sponsor categories across breast cancer and lung cancer trials"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

<details>
<summary><strong>Pfizer vs Novartis oncology by phase</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare Pfizer vs Novartis oncology trials by phase"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>

### Network

<details>
<summary><strong>Diabetes sponsor and drug network — network_graph, 2619 nodes, 5422 edges, 1000 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show a network of sponsors and drugs for diabetes trials"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | network_graph |
| Title | Diabetes sponsor–drug–condition network |
| Data | 2619 nodes, 5422 edges |
| Studies fetched | 1000 |
| Time granularity | — |
| Filters applied | condition=diabetes |

**Full response**

Saved to [`examples/live/network_diabetes_sponsor_drug.json`](examples/live/network_diabetes_sponsor_drug.json) (2,494,403 bytes).

<details>
<summary>Preview (first 40 lines)</summary>

```json
{
  "visualization": {
    "type": "network_graph",
    "encoding": {
      "nodes": "nodes",
      "edges": "edges"
    },
    "data": {
      "nodes": [
        {
          "id": "steen-andersen",
          "label": "Steen Andersen",
          "citations": [
            {
              "nct_id": "NCT01454700",
              "excerpt": "Steen Andersen"
            }
          ]
        },
        {
          "id": "insulin-pump-therapy-csii-plus-continuous-glucose-monitoring-cgm",
          "label": "Insulin pump therapy (CSII) plus continuous glucose monitoring (CGM)",
          "citations": [
            {
              "nct_id": "NCT01454700",
              "excerpt": "Insulin pump therapy (CSII) plus continuous glucose monitoring (CGM)"
            }
          ]
        },
        {
          "id": "multiple-daily-insulin-injections-mdi",
          "label": "Multiple daily insulin injections (MDI)",
          "citations": [
            {
              "nct_id": "NCT01454700",
              "excerpt": "Multiple daily insulin injections (MDI)"
            }
          ]
        },
        {
...
```

</details>

</details>

<details>
<summary><strong>Melanoma drug co-occurrence network</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which drugs frequently co-occur in combination melanoma trials?"
  }'
```

**Response**

_Capture with the curl above, save JSON, then re-render with `scripts/render_readme_example.py --json <path>`._

</details>
