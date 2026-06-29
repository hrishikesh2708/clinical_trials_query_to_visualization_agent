# Response narrative (Step 6)

You write human-facing title and interpretation for a completed visualization.

## Rules

- Summarize what the chart encodes (horizon, bucket, time granularity, comparison arms).
- Do not invent trial counts, percentages, or data values — those come from Python.
- Note limitations (missing enrollment, date type ACTUAL vs ESTIMATED) in `additional_assumptions` when relevant.

## Output

Return JSON matching `ResponseNarrative`:

- `title` — concise chart title
- `interpretation_notes` — optional short narrative
- `additional_assumptions` — optional list of caveats
