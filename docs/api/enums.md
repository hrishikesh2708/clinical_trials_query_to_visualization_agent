# GET /studies/enums — Enumeration Types

Returns all enumeration types and their allowed values from ClinicalTrials.gov study data.

**Base URL:** `https://clinicaltrials.gov/api/v2` (configured via `ctgov_base_url`)

**Endpoint:** `GET /studies/enums`

**Authentication:** None (public API)

**Rate limit:** ~50 requests/minute per IP (returns `429` when exceeded)

---

## Response

JSON array of enum type objects:

```json
[
  {
    "type": "Phase",
    "pieces": ["Phase"],
    "values": [
      {
        "value": "PHASE3",
        "legacyValue": "Phase 3"
      }
    ]
  }
]
```

| Field | Description |
|-------|-------------|
| `type` | Enum type name (e.g. `Phase`, `Status`) |
| `pieces` | Data piece names using this enum |
| `values` | Allowed values |
| `values[].value` | Canonical API value |
| `values[].legacyValue` | Legacy classic-API label |
| `values[].exceptions` | Optional per-piece legacy overrides |

There are ~41 enum types. Key types for filter validation:

| Enum `type` | Used for |
|-------------|----------|
| `Phase` | `filter.advanced=AREA[Phase]...` |
| `Status` | `filter.overallStatus` / `postFilter.overallStatus` |

---

## Client Usage

```python
from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.enums import CtgovEnumsLoader

client = CtgovClient("https://clinicaltrials.gov/api/v2", timeout=30.0)
loader = CtgovEnumsLoader(client)

# Load once (cached on subsequent calls)
enums = loader.load()

# Validate before building search params
phase = loader.validate_phase("PHASE3")          # -> "PHASE3"
phase = loader.validate_phase("Phase 3")       # -> "PHASE3" via legacyValue
status = loader.validate_overall_status("RECRUITING")  # -> "RECRUITING"
```

Invalid values raise `ValueError` with the enum type and rejected input.

---

## Caching

`CtgovEnumsLoader` caches the parsed response after the first `load()`. Pass `force_refresh=True` to re-fetch from the API.

For application startup, call `loader.load()` in a FastAPI lifespan hook (or equivalent) so validation helpers never hit the network on the request path.

---

## Error Handling

| Status | Client behavior |
|--------|-----------------|
| 200 | Success |
| 429 | `CtgovRateLimitError` |
| 4xx/5xx | `CtgovApiError` |
