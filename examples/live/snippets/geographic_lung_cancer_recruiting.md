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
