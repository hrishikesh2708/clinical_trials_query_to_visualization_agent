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

## API usage

Sample request (time trend — matches [examples/time_trend_pembrolizumab.json](examples/time_trend_pembrolizumab.json)):

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

Five pre-generated responses in [examples/](examples/):

| File | Horizon | Query theme |
|------|---------|-------------|
| `time_trend_pembrolizumab.json` | time_trend | Pembrolizumab trials per year since 2015 |
| `distribution_breast_cancer_phase.json` | distribution | Breast cancer by phase |
| `comparison_pembrolizumab_vs_nivolumab.json` | comparison | Pembrolizumab vs nivolumab |
| `geographic_lung_cancer_recruiting.json` | geographic | Recruiting lung cancer by country |
| `network_diabetes_sponsor_drug.json` | network | Diabetes sponsor–drug network |

These files are produced from **mocked pipeline runs** using captured API fixtures in `tests/fixtures/api/`, not live ClinicalTrials.gov calls. Regenerate with:

```bash
uv run python scripts/generate_examples.py
```

## Submission package checklist

**Include in zip:**

- All source code (`app/`, `tests/`, `scripts/`, `docs/`, `examples/`, `pyproject.toml`, `.env.example`, etc.)
- Complete README
- 3–5 example JSON files in `examples/` (5 present)

**Exclude:**

- `.venv/`, `.env`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- `response_dumps/*.json` (gitignored; see [.gitignore](.gitignore))

**Optional zip command:**

```bash
zip -r clinicaltrials-agent.zip . \
  -x '.venv/*' -x '.env' -x 'response_dumps/*' \
  -x '__pycache__/*' -x '.pytest_cache/*' -x '.ruff_cache/*'
```

{
  "query": "How has the number of trials for this drug changed over time?",
  "drug_name": "Pembrolizumab",
  "condition": null,
  "trial_phase": null,
  "sponsor": null,
  "country": null,
  "start_year": null,
  "end_year": null
}

{
  "query": "How has the number of trials for Pembrolizumab changed per year since 2015",
  "drug_name": null,
  "condition": null,
  "trial_phase": null,
  "sponsor": null,
  "country": null,
  "start_year": null,
  "end_year": null
}

{
  "query": "How has the number of trials for Pembrolizumab changed per year between 2015 to 2018",
  "drug_name": null,
  "condition": null,
  "trial_phase": null,
  "sponsor": null,
  "country": null,
  "start_year": null,
  "end_year": null
}

{
  "query": "How many trials started each year for diabetes",
  "drug_name": null,
  "condition": null,
  "trial_phase": null,
  "sponsor": null,
  "country": null,
  "start_year": null,
  "end_year": null
}