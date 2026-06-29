# GET /studies/metadata — Study Data Model Fields

Returns the study data model field tree: names, types, and hierarchy. Essential for knowing which fields exist before horizon/mapper design and for selecting `fields` in search/get requests.

**Base URL:** `https://clinicaltrials.gov/api/v2` (configured via `ctgov_base_url`)

**Endpoint:** `GET /studies/metadata`

**Authentication:** None (public API)

**Rate limit:** ~50 requests/minute per IP (returns `429` when exceeded)

---

## Query Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `includeIndexedOnly` | `false` | Include indexed-only fields (~77 extra leaves vs default) |
| `includeHistoricOnly` | `false` | Include fields available only in historic data |

---

## Response

JSON array of root field nodes (recursive tree). Six top-level areas by default:

- `ProtocolSection`
- `ResultsSection`
- `AnnotationSection`
- `DocumentSection`
- `DerivedSection`
- `HasResults`

### Node schema

| Property | Description |
|----------|-------------|
| `name` | JSON key name (camelCase) |
| `piece` | Name used in `fields` query param (PascalCase) |
| `title` | Human-readable label |
| `sourceType` | `STRUCT` for branches; leaf types vary |
| `type` | Data type or enum reference (`TEXT`, `DATE`, `Status`, `Phase[]`, `MARKUP`, …) |
| `dedLink` | Optional link to field definition |
| `children` | Nested nodes (absent on leaves) |

Example leaf:

```json
{
  "name": "nctId",
  "piece": "NCTId",
  "title": "National Clinical Trial (NCT) Identification Number",
  "sourceType": "TEXT",
  "type": "nct"
}
```

---

## Relation to `fields` param

The `fields` parameter on [`GET /studies`](studies.md) and [`GET /studies/{nctId}`](study-by-nct-id.md) accepts `piece` names from this tree:

| Selection | Effect |
|-----------|--------|
| Branch (`ProtocolSection`, `ConditionsModule`) | Returns all descendant fields |
| Leaf (`NCTId`, `OverallStatus`, `Phase`) | Returns only that field — minimal payload |

Use `StudyMetadata.field_pieces()` to list all valid leaf piece names programmatically.

---

## Client Usage

```python
from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.metadata import MetadataParams

client = CtgovClient("https://clinicaltrials.gov/api/v2", timeout=30.0)

metadata = client.get_metadata()
pieces = metadata.field_pieces()  # all leaf field names

# Include indexed-only fields for search-area discovery
indexed = client.get_metadata(MetadataParams(include_indexed_only=True))
```

---

## Error Handling

| Status | Client behavior |
|--------|-----------------|
| 200 | Success |
| 429 | `CtgovRateLimitError` |
| 4xx/5xx | `CtgovApiError` |
