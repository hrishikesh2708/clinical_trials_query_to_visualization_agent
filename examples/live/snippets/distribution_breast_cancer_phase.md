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
