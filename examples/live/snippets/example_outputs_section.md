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
<summary><strong>time_trend_pembrolizumab — time_series, 13 data rows, 1000 studies</strong></summary>

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
<summary><strong>distribution_breast_cancer_phase — bar_chart, 7 data rows, 1000 studies</strong></summary>

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
<summary><strong>comparison_pembrolizumab_vs_nivolumab — grouped_bar_chart, 14 data rows, 2000 studies</strong></summary>

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
<summary><strong>geographic_lung_cancer_recruiting — bar_chart, 68 data rows, 1000 studies</strong></summary>

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
<summary><strong>network (fixture-backed; live returns 422 pending citation fix) — network_graph, 56 nodes, 74 edges, 15 studies</strong></summary>

**Request**

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Diabetes sponsor and drug network"
  }'
```

**Response summary**

| Field | Value |
|-------|-------|
| Visualization | network_graph |
| Title | Sponsor–drug network for diabetes trials |
| Data | 56 nodes, 74 edges |
| Studies fetched | 15 |
| Time granularity | — |
| Filters applied | condition=diabetes |

**Full response**

Saved to [`examples/network_diabetes_sponsor_drug.json`](examples/network_diabetes_sponsor_drug.json) (39,759 bytes).

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

