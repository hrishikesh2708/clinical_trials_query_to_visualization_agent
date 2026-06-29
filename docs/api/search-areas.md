# GET /studies/search-areas — Search Area Definitions

Returns search documents and their search areas. Defines which study fields each `query.*` parameter searches — essential for Stage 8 query planner logic.

**Base URL:** `https://clinicaltrials.gov/api/v2` (configured via `ctgov_base_url`)

**Endpoint:** `GET /studies/search-areas`

**Authentication:** None (public API)

**Rate limit:** ~50 requests/minute per IP (returns `429` when exceeded)

---

## Response

JSON array of search documents. Currently one document:

```json
[
  {
    "name": "Study",
    "areas": [
      {
        "name": "ConditionSearch",
        "uiLabel": "Conditions or disease",
        "param": "cond",
        "parts": [
          {
            "pieces": ["Condition"],
            "type": "text",
            "isEnum": false,
            "isSynonyms": true,
            "weight": 0.95
          }
        ]
      }
    ]
  }
]
```

### Document schema

| Field | Description |
|-------|-------------|
| `name` | Document name (e.g. `Study`) |
| `areas` | List of search areas |

### Area schema

| Field | Description |
|-------|-------------|
| `name` | Area identifier (e.g. `ConditionSearch`, `BasicSearch`) |
| `uiLabel` | Human label shown in the CT.gov UI |
| `param` | Slug used in `query.{param}` (empty for internal sub-areas) |
| `parts` | Indexed field groups with relevance weights |

### Part schema

| Field | Description |
|-------|-------------|
| `pieces` | Field piece names searched in this part |
| `type` | Data type (`text`, `nct`, enum name, etc.) |
| `isEnum` | Whether the part uses enumerated values |
| `isSynonyms` | Whether synonym expansion applies |
| `weight` | Relevance weight (higher = more important in ranking) |

---

## Relation to `query.*` params

Areas with a non-empty `param` map directly to [`GET /studies`](studies.md) query parameters:

| Area | `param` | HTTP key | `StudiesSearchParams` field |
|------|---------|----------|----------------------------|
| `ConditionSearch` | `cond` | `query.cond` | `query_cond` |
| `InterventionSearch` | `intr` | `query.intr` | `query_intr` |
| `BasicSearch` | `term` | `query.term` | `query_term` |
| `LocationSearch` | `locn` | `query.locn` | `query_locn` |
| `TitleSearch` | `titles` | `query.titles` | `query_titles` |
| `OutcomeSearch` | `outc` | `query.outc` | `query_outc` |
| `SponsorSearch` | `spons` | `query.spons` | `query_spons` |
| `IdSearch` | `id` | `query.id` | `query_id` |
| `PatientSearch` | `patient` | `query.patient` | `query_patient` |

Areas with empty `param` (e.g. `InterventionNameSearch`, `NCTIdSearch`) are internal indexing subdivisions, not separate HTTP query params.

---

## Client Usage

```python
from app.infrastructure.ctgov.client import CtgovClient

client = CtgovClient("https://clinicaltrials.gov/api/v2", timeout=30.0)
areas = client.get_search_areas()

# Planner helpers (Stage 8)
cond_area = areas.area_for_param("cond")
query_key = areas.query_param_key("cond")  # "query.cond"
searchable = areas.areas_with_params()
```

---

## Error Handling

| Status | Client behavior |
|--------|-----------------|
| 200 | Success |
| 429 | `CtgovRateLimitError` |
| 4xx/5xx | `CtgovApiError` |
