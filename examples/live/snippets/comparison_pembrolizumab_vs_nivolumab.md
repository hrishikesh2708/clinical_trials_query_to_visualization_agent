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
