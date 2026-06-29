# GET /studies — Search Studies

Search ClinicalTrials.gov study records. This is the primary workhorse endpoint for the agent.

**Base URL:** `https://clinicaltrials.gov/api/v2` (configured via `ctgov_base_url`)

**Endpoint:** `GET /studies`

**Authentication:** None (public API)

**Rate limit:** ~50 requests/minute per IP (returns `429` when exceeded)

---

## Query Parameters

### Format

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | enum | `json` | `json` or `csv` |
| `markupFormat` | enum | `markdown` | `markdown` or `legacy` (JSON only) |

### Search (Essie expression syntax)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `query.cond` | Conditions or disease | `lung cancer`, `(head OR neck) AND pain` |
| `query.term` | Other terms (full-text) | `AREA[LastUpdatePostDate]RANGE[2023-01-15,MAX]` |
| `query.locn` | Location terms | `Boston, Massachusetts` |
| `query.titles` | Title / acronym | `diabetes prevention` |
| `query.intr` | Intervention / treatment | `Pembrolizumab` |
| `query.outc` | Outcome measure | — |
| `query.spons` | Sponsor / collaborator | `National Cancer Institute` |
| `query.lead` | Lead sponsor name | — |
| `query.id` | Study IDs | — |
| `query.patient` | Patient search area | — |

### Pre-filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `filter.overallStatus` | comma/pipe-separated list | `RECRUITING`, `COMPLETED`, etc. |
| `filter.geo` | string | `distance(lat,lon,dist)` e.g. `distance(39.0035707,-77.1013313,50mi)` |
| `filter.ids` | comma/pipe-separated NCT IDs | `NCT04852770,NCT01728545` |
| `filter.advanced` | Essie expression | `AREA[Phase]PHASE3`, `AREA[StartDate]2022` |
| `filter.synonyms` | comma/pipe-separated pairs | `ConditionSearch:1651367` |

**Valid `filter.overallStatus` values:** `ACTIVE_NOT_RECRUITING`, `COMPLETED`, `ENROLLING_BY_INVITATION`, `NOT_YET_RECRUITING`, `RECRUITING`, `SUSPENDED`, `TERMINATED`, `WITHDRAWN`, `AVAILABLE`, `NO_LONGER_AVAILABLE`, `TEMPORARILY_NOT_AVAILABLE`, `APPROVED_FOR_MARKETING`, `WITHHELD`, `UNKNOWN`

**Phase filtering:** There is no `filter.phase` parameter. Use `filter.advanced`:

```
filter.advanced=AREA[Phase]PHASE3
filter.advanced=AREA[Phase]PHASE2 OR AREA[Phase]PHASE3
```

Valid phase values: `EARLY_PHASE1`, `PHASE1`, `PHASE2`, `PHASE3`, `PHASE4`, `NA`

### Post-filters

Same shapes as pre-filters, applied after search ranking:

| Parameter | Type |
|-----------|------|
| `postFilter.overallStatus` | comma/pipe-separated list |
| `postFilter.geo` | `distance(...)` |
| `postFilter.ids` | comma/pipe-separated NCT IDs |
| `postFilter.advanced` | Essie expression |
| `postFilter.synonyms` | area:synonym_id pairs |

### Aggregation / geo

| Parameter | Default | Description |
|-----------|---------|-------------|
| `aggFilters` | — | `filter_id:option_keys` e.g. `status:not rec,sex:f` |
| `geoDecay` | `func:exp,scale:300mi,offset:0mi,decay:0.5` | Proximity decay for `filter.geo` |

### Projection

| Parameter | Description |
|-----------|-------------|
| `fields` | Comma/pipe-separated field list; omit for all fields. Special: `@query` |
| `sort` | Max 2 items; e.g. `LastUpdatePostDate:desc`, `@relevance` |
| `countTotal` | `true` to include `totalCount` on first page |

### Pagination

| Parameter | Default | Constraints |
|-----------|---------|-------------|
| `pageSize` | 10 | Max 1000; coerced down if greater |
| `pageToken` | — | Omit on first page; use `nextPageToken` from prior response |

**Client pagination cap:** `pagination_cap` in settings (default 1000) limits total studies collected by `iter_search_studies`.

---

## Response (JSON)

```json
{
  "studies": [
    {
      "protocolSection": { ... },
      "derivedSection": { ... },
      "hasResults": false
    }
  ],
  "nextPageToken": "opaque-token",
  "totalCount": 1234
}
```

| Field | Presence |
|-------|----------|
| `studies` | Always (may be empty) |
| `nextPageToken` | Present when more pages exist |
| `totalCount` | Only when `countTotal=true` on first page |

**Pagination flow:**

1. First request: omit `pageToken`
2. If `nextPageToken` is present, pass it as `pageToken` on the next request
3. Stop when `nextPageToken` is absent

---

## Error Handling

| Status | Body | Client behavior |
|--------|------|-----------------|
| 200 | JSON | Success |
| 400 | Plain text (often) | `CtgovApiError` — unknown param, invalid value |
| 429 | — | `CtgovRateLimitError` |
| 5xx | varies | `CtgovApiError` |
| Timeout | — | `httpx.TimeoutException` propagates |

Example 400: `` `filter.phase` is unknown parameter ``

---

## Client Usage

```python
from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.models import StudiesSearchParams

client = CtgovClient("https://clinicaltrials.gov/api/v2", timeout=30.0)

# Single page
result = client.search_studies(
    StudiesSearchParams(
        query_cond="diabetes",
        filter_overall_status=["RECRUITING"],
        fields=["NCTId", "BriefTitle"],
        page_size=100,
    )
)

# Phase via convenience builder
params = StudiesSearchParams.with_phases(
    ["PHASE3"],
    query_cond="diabetes",
    page_size=50,
)

# Auto-paginate (up to pagination_cap)
for study in client.iter_search_studies(params):
    nct_id = study["protocolSection"]["identificationModule"]["nctId"]
```
