# GET /studies/{nctId} — Single Study

Returns the full record for one clinical trial. Used for deep citations with exact field excerpts.

**Base URL:** `https://clinicaltrials.gov/api/v2` (configured via `ctgov_base_url`)

**Endpoint:** `GET /studies/{nctId}`

**Authentication:** None (public API)

**Rate limit:** ~50 requests/minute per IP (returns `429` when exceeded)

---

## Path Parameter

| Parameter | Pattern | Description |
|-----------|---------|-------------|
| `nctId` | `^[Nn][Cc][Tt]0*[1-9]\d{0,7}$` | NCT Number (e.g. `NCT00841061`, `NCT04000165`) |

If the ID matches an `NCTIdAlias` field, the API returns a **301 redirect** to the canonical study URL. The client follows redirects automatically (httpx default).

The client validates `nctId` against the pattern before sending a request and raises `ValueError` for invalid IDs.

---

## Query Parameters

| Parameter | Type | Default | Allowed |
|-----------|------|---------|---------|
| `format` | enum | `json` | `csv`, `json`, `json.zip`, `fhir.json`, `ris` |
| `markupFormat` | enum | `markdown` | `markdown`, `legacy` (JSON only) |
| `fields` | comma/pipe-separated list | all fields | area, piece, or field names |

### Format options

| Value | Response |
|-------|----------|
| `json` | Single study JSON object |
| `csv` | CSV table (columns per CSV Download page) |
| `json.zip` | JSON file in zip archive |
| `fhir.json` | FHIR JSON (fields not customizable) |
| `ris` | RIS record (tags per RIS Download page) |

### Fields

For JSON, each item is an area name, piece name, or field name. Branch nodes include all descendants. Omit `fields` to return the full study record.

Examples: `NCTId,BriefTitle,Reference` or `ConditionsModule,EligibilityModule`

---

## Response (JSON)

Unlike search (`GET /studies`), the response is a **single study object**, not wrapped in a `studies` array:

```json
{
  "protocolSection": { ... },
  "derivedSection": { ... },
  "hasResults": false
}
```

---

## Error Handling

| Status | Body | Client behavior |
|--------|------|-----------------|
| 200 | JSON | Success |
| 301 | — | Redirect to canonical NCT ID (followed automatically) |
| 400 | Plain text (often) | `CtgovApiError` |
| 404 | — | `CtgovApiError` — study not found |
| 429 | — | `CtgovRateLimitError` |
| 5xx | varies | `CtgovApiError` |
| Timeout | — | `httpx.TimeoutException` propagates |

---

## Client Usage

```python
from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.models import StudyGetParams

client = CtgovClient("https://clinicaltrials.gov/api/v2", timeout=30.0)

# Full study record
study = client.get_study("NCT04852770")

# Field-scoped fetch for citations
study = client.get_study(
    "NCT04852770",
    StudyGetParams(fields=["NCTId", "BriefTitle", "Reference"]),
)

nct_id = study["protocolSection"]["identificationModule"]["nctId"]
title = study["protocolSection"]["identificationModule"]["briefTitle"]
```
