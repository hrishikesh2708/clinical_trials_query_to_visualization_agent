# Field observations from raw API dumps

Notes from reviewing local captures under `response_dumps/` (run `20260629T111213` and `20260629T111241`). These inform Stage 4 horizon-matrix brainstorming; no matrix decisions are finalized here.

**Source dumps referenced below:**

| Dump file | Endpoint |
|-----------|----------|
| `studies_pembrolizumab_20260629T111213.json` | `GET /studies` (intervention search) |
| `studies_breast_cancer_20260629T111213.json` | `GET /studies` (condition search) |
| `studies_obscure_20260629T111213.json` | `GET /studies` (near-empty) |
| `studies_pembrolizumab_page2_20260629T111213.json` | `GET /studies` (pagination) |
| `study_NCT03725059_20260629T111213.json` | `GET /studies/{nctId}` |
| `enums_20260629T111213.json` | `GET /studies/enums` |
| `metadata_20260629T111241.json` | `GET /studies/metadata` |

---

## 1. Time / trend candidates

| JSON path | Observed in | Notes |
|-----------|-------------|-------|
| `studies[].protocolSection.statusModule.startDateStruct.date` | `studies_pembrolizumab_*` | ISO date string (e.g. `"2024-06-10"`); paired with `.type` (`ACTUAL` / `ESTIMATED`) |
| `studies[].protocolSection.statusModule.primaryCompletionDateStruct.date` | `studies_pembrolizumab_*` | Same `{date, type}` struct |
| `studies[].protocolSection.statusModule.completionDateStruct.date` | `studies_pembrolizumab_*` | Study completion; same struct |
| `studies[].protocolSection.statusModule.studyFirstSubmitDate` | `studies_pembrolizumab_*` | Plain date string (e.g. `"2024-05-15"`), not a struct |
| `studies[].protocolSection.statusModule.studyFirstPostDateStruct.date` | `studies_pembrolizumab_*` | First public posting; `{date, type}` |
| `studies[].protocolSection.statusModule.lastUpdatePostDateStruct.date` | `studies_pembrolizumab_*` | Registry last update; good for “freshness” trends |

Metadata piece for start date: `StartDateStruct` (from `metadata_*`, node `startDateStruct`).

**Open questions for Stage 4:** Which date drives “trials per year” — `startDateStruct`, `studyFirstPostDateStruct`, or `studyFirstSubmitDate`? How to handle `ACTUAL` vs `ESTIMATED`? See [§8](#8-stage-4-pre-read-official-semantics-vs-product-decisions).

---

## 2. Phase / status

| JSON path | Observed in | Notes |
|-----------|-------------|-------|
| `studies[].protocolSection.designModule.phases` | `studies_pembrolizumab_*` | Array of API codes, e.g. `["PHASE3"]` (not display labels) |
| `studies[].protocolSection.statusModule.overallStatus` | `studies_pembrolizumab_*` | Single string, e.g. `"RECRUITING"` |
| `studies[].protocolSection.contactsLocationsModule.locations[].status` | `studies_pembrolizumab_*` | Per-site status (e.g. `"RECRUITING"`), distinct from overall status |

Enum formats (`enums_*`):

- **Phase:** `value` codes like `PHASE3`, `PHASE2`; `legacyValue` is human label (e.g. `"Phase 3"`).
- **Status:** `value` codes like `RECRUITING`, `COMPLETED`; `legacyValue` is display text.

**Open questions:** Multi-phase trials return multiple `phases` entries — bucket as primary phase or explode? Map enum codes via `/studies/enums` in mappers (Stage 6). See [§8](#8-stage-4-pre-read-official-semantics-vs-product-decisions).

---

## 3. Geography

| JSON path | Observed in | Notes |
|-----------|-------------|-------|
| `studies[].protocolSection.contactsLocationsModule.locations[]` | `studies_pembrolizumab_*` | Large array per study (e.g. 212 sites for NCT06422143 in search hit) |
| `…locations[].country` | `studies_pembrolizumab_*` | e.g. `"United States"` |
| `…locations[].city`, `…state`, `…zip` | `studies_pembrolizumab_*` | Present on US sites |
| `…locations[].geoPoint.lat` / `.lon` | `studies_pembrolizumab_*` | Numeric coordinates for geo filters |
| `…locations[].facility` | `studies_pembrolizumab_*` | Site name string |

**Open questions:** Country-level charts may need deduplication (one study, many locations). `filter.geo` uses `distance(lat,lon,dist)` per API docs — confirm against search-area params in Stage 4. See [§8](#8-stage-4-pre-read-official-semantics-vs-product-decisions).

---

## 4. Interventions / sponsors

| JSON path | Observed in | Notes |
|-----------|-------------|-------|
| `studies[].protocolSection.armsInterventionsModule.interventions[]` | `studies_pembrolizumab_*` | Each: `type`, `name`, `description`, `armGroupLabels`, `otherNames` |
| `…interventions[].name` | `studies_pembrolizumab_*` | e.g. `"Pembrolizumab"` — primary drug label for intervention search |
| `…interventions[].otherNames` | `studies_pembrolizumab_*` | Synonyms (e.g. `KEYTRUDA®`, `MK-3475`) |
| `studies[].protocolSection.sponsorCollaboratorsModule.leadSponsor.name` | `studies_pembrolizumab_*` | e.g. `"Merck Sharp & Dohme LLC"` |
| `…leadSponsor.class` | `studies_pembrolizumab_*` | e.g. `"INDUSTRY"` |
| `…sponsorCollaboratorsModule.collaborators` | `study_NCT03725059_*` | `null` on sampled study — optional array |

Conditions (for drug–condition edges):

| JSON path | Observed in | Notes |
|-----------|-------------|-------|
| `studies[].protocolSection.conditionsModule.conditions` | `studies_pembrolizumab_*` | String array, e.g. `["Non-small Cell Lung Cancer", "NSCLC"]` |

---

## 5. Network graph candidates

| Relationship | JSON paths | Notes |
|--------------|------------|-------|
| Drug → condition | `armsInterventionsModule.interventions[].name` → `conditionsModule.conditions[]` | Direct from protocol section |
| Drug → MeSH | `derivedSection.interventionBrowseModule.meshes[]` | e.g. `{id: "C582435", term: "pembrolizumab"}` in `study_NCT03725059_*` |
| Condition → MeSH | `derivedSection.conditionBrowseModule.meshes[]` | e.g. `{id: "D001943", term: "Breast Neoplasms"}` |
| Sponsor → trial | `sponsorCollaboratorsModule.leadSponsor.name` → `identificationModule.nctId` | One lead sponsor per study in samples |

`derivedSection` appears on every sampled study (`protocolSection`, `derivedSection`, `hasResults` at top level).

---

## 6. Surprises / structural notes

| Topic | Observed in | Detail |
|-------|-------------|--------|
| Near-empty search | `studies_obscure_*` | `{"studies": []}` — no `totalCount` when obscure term matches nothing |
| Pagination | `studies_pembrolizumab_*`, `studies_pembrolizumab_page2_*` | `totalCount: 2890`, default page 100 studies; `nextPageToken` opaque string; page 2 used `pageSize=5` |
| Study size | `studies_pembrolizumab_*` | ~11 MB for 100 full studies — default search returns large nested objects |
| Top-level study shape | `study_NCT03725059_*` | `protocolSection`, `derivedSection`, `hasResults` (boolean) |
| Enrollment | `study_NCT03725059_*` | `protocolSection.designModule.enrollmentInfo` → `{count, type}` (e.g. `ESTIMATED`) |
| Text fields | `study_NCT03725059_*` | `descriptionModule.briefSummary` is plain text in sample (markupFormat=markdown default) |
| Metadata gaps | `metadata_*` | Some nodes omit `title` — strict Pydantic parse fails; raw dump preferred for exploration |
| NCT ID in search hits | `studies_pembrolizumab_*` | `protocolSection.identificationModule.nctId` — reliable for follow-up `get_study` |

---

## 7. Search areas (query param mapping)

From `search_areas_20260629T111242.json` (not repeated here): intervention area maps to `query.intr`, condition to `query.cond`, etc. Confirms `StudiesSearchParams` field names align with API (`query_intr` → `query.intr`).

`LocationSearch` (`param: "locn"`) searches `LocationCity`, `LocationState` (`GeoName`), `LocationCountry`, `LocationFacility`, `LocationZip` — text/location search, not radius filtering.

---

## 8. Stage 4 pre-read (official semantics vs product decisions)

Cross-checked open questions against `metadata_*`, `enums_*`, `search_areas_*`, and [protocol field definitions](https://clinicaltrials.gov/policy/protocol-definitions). The [study data structure glossary](https://clinicaltrials.gov/data-api/about-api/study-data-structure) mirrors this; machine-readable sources above are preferable to scraping that page.

### Dates — what each field means (resolved)

| Field | Official meaning (`metadata_*`) | Use when the question is about… |
|-------|--------------------------------|--------------------------------|
| `startDateStruct.date` | Study start — recruitment opens / first enrollment | **When trials started** (clinical timeline) |
| `studyFirstSubmitDate` | Sponsor first submitted record to CT.gov | Internal registration timeline |
| `studyFirstPostDateStruct.date` | Record first appeared on CT.gov after QC | **Public registry appearance** |

Metadata notes a lag between submit and first-posted dates — they are not interchangeable.

`DateType` enum (`enums_*`): `ACTUAL` and `ESTIMATED` (legacy `Anticipated` maps to `ESTIMATED` for `StartDateType`). Docs define values but do not prescribe trend-chart policy.

**Stage 4 decision:** Pick canonical date per horizon. Default lean for “trials per year since 2015”: `startDateStruct.date`. Document `ACTUAL`/`ESTIMATED` inclusion rule (e.g. include both, or prefer `ACTUAL` when present).

### Phases — structure resolved, aggregation not

`phases` is `Phase[]`; metadata rules note PRS allows combo selections (e.g. Phase 1/2, Phase 2/3). Multiple entries are valid API data.

Enum codes (`PHASE1`, `PHASE2`, …) map to display labels via `/studies/enums` — defer to Stage 6 mappers.

**Stage 4 decision:** Explode (count in each phase bucket), primary/first only, or treat combos as own labels. Docs do not choose.

### Geography — `query.locn` vs `filter.geo` (resolved)

| Mechanism | Param | Purpose |
|-----------|-------|---------|
| Location search | `query.locn` | Text search over city/state/country/facility/zip (`search_areas_*` → `LocationSearch`) |
| Proximity pre-filter | `filter.geo` | `distance(lat,lon,dist)` on `/studies` ([`studies.md`](studies.md)) — not a search-area param |

Each study has many `locations[]` entries; official structure does not define chart aggregation.

**Stage 4 decision:** Country-level charts need an explicit dedup rule (e.g. one count per study per unique `locations[].country`).

### Summary

| Open question | Resolved by official docs? | Stage 4 action |
|---------------|---------------------------|----------------|
| What does each date mean? | Yes | Pick canonical field per horizon |
| `ACTUAL` vs `ESTIMATED` | Partially (enum values only) | Write inclusion rule |
| Multi-phase representation | Partially (multi-value allowed) | Pick explode / primary / combo |
| Enum display codes | Yes (`/studies/enums`) | Defer mapping to Stage 6 |
| `filter.geo` vs `query.locn` | Yes (different params) | Document when each is used |
| Country dedup for charts | No | Define aggregation rule |

---

## Next step (Stage 4)

Use sections 1–7 for observed paths and section 8 for semantics vs decisions. Draft `docs/horizon_matrix.md` and `app/domain/horizons.py`: canonical date field, phase bucketing, geography aggregation level, and which modules are in scope for each visualization horizon.
