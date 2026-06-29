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
