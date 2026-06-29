<details>
<summary><strong>Network — Diabetes sponsor–drug network (fixture-backed; live 422 pending citation fix) — network_graph, 56 nodes, 74 edges, 15 studies</strong></summary>

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
