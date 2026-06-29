# Example outputs

| Kind | Location | Notes |
|------|----------|-------|
| Live captures | [`live/`](live/) | Real `POST /api/v1/visualize` responses (see root README) |
| Test fixtures | [`*.json`](.) | Mocked pipeline runs; regenerate with `uv run python scripts/generate_examples.py` |

## Render collapsible README blocks

```bash
# Single example (paste stdout into README)
uv run python scripts/render_readme_example.py \
  --title "Time trend — Pembrolizumab since 2015" \
  --curl-file live/curls/time_trend_pembrolizumab.sh \
  --json live/time_trend_pembrolizumab.json

# Regenerate the Sample queries section
uv run python scripts/render_sample_queries_section.py
```

Edit [`live/sample_queries/manifest.json`](live/sample_queries/manifest.json) to add queries; set `"json"` when you have a captured response file.
