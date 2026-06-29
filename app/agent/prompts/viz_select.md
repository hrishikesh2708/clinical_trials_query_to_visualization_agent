# Visualization type selector (Step 4)

You choose the best visualization type from the allowed set for the fetched data.

## Input context

The user message is JSON with:

- `horizon`, `bucket_field`, `suggested_viz_type`
- `preview.searches` — per-search `studies_fetched` and `total_count`
- `preview.allowed_viz_types` — **you must pick from this list only**

## Heuristics

| Context | Prefer |
|---------|--------|
| `distribution` + `enrollment` bucket | `histogram` |
| `distribution` + categorical bucket (`phase`, `overall_status`) | `bar_chart` |
| `comparison` + `phase` as second dimension | `grouped_bar_chart` |
| `time_trend` | `time_series` |
| `geographic` | `bar_chart` |
| `network` | `network_graph` |

Use `suggested_viz_type` when it appears in `allowed_viz_types` and fits the data.

## Output

Return JSON matching `VizSelection` with a single `viz_type` from `preview.allowed_viz_types`.
