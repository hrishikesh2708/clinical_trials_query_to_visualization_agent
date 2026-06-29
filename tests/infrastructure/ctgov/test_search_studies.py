import pytest

from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.models import StudiesSearchParams
from tests.infrastructure.ctgov.conftest import mock_ctgov_urlopen, query_param

BASE_URL = "https://clinicaltrials.gov/api/v2"
STUDY_STUB = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT00000001",
            "briefTitle": "Test Study",
        }
    },
    "hasResults": False,
}


def _client(pagination_cap: int = 1000) -> CtgovClient:
    return CtgovClient(BASE_URL, timeout=5.0, pagination_cap=pagination_cap)


def test_search_studies_builds_full_query_string() -> None:
    params = StudiesSearchParams(
        query_cond="diabetes",
        query_term="metformin",
        query_locn="California",
        query_titles="prevention",
        query_intr="insulin",
        query_outc="HbA1c",
        query_spons="NCI",
        query_lead="Pfizer",
        query_id="NCT00000001",
        query_patient="adult",
        filter_overall_status=["RECRUITING", "COMPLETED"],
        filter_geo="distance(39.0,-77.1,50mi)",
        filter_ids=["NCT00000001", "NCT00000002"],
        filter_advanced="AREA[Phase]PHASE3",
        filter_synonyms=["ConditionSearch:1651367"],
        post_filter_overall_status=["RECRUITING"],
        post_filter_geo="distance(40.0,-74.0,25mi)",
        post_filter_ids=["NCT00000003"],
        post_filter_advanced="AREA[StartDate]2022",
        post_filter_synonyms=["BasicSearch:2013558"],
        agg_filters="status:not rec,sex:f",
        geo_decay="func:linear,scale:100km,offset:10km,decay:0.1",
        fields=["NCTId", "BriefTitle"],
        sort=["LastUpdatePostDate:desc", "@relevance"],
        count_total=True,
        page_size=50,
        page_token="token-abc",
    )

    query = params.to_query_params()

    assert query["query.cond"] == "diabetes"
    assert query["query.term"] == "metformin"
    assert query["query.locn"] == "California"
    assert query["query.titles"] == "prevention"
    assert query["query.intr"] == "insulin"
    assert query["query.outc"] == "HbA1c"
    assert query["query.spons"] == "NCI"
    assert query["query.lead"] == "Pfizer"
    assert query["query.id"] == "NCT00000001"
    assert query["query.patient"] == "adult"
    assert query["filter.overallStatus"] == "RECRUITING,COMPLETED"
    assert query["filter.geo"] == "distance(39.0,-77.1,50mi)"
    assert query["filter.ids"] == "NCT00000001,NCT00000002"
    assert query["filter.advanced"] == "AREA[Phase]PHASE3"
    assert query["filter.synonyms"] == "ConditionSearch:1651367"
    assert query["postFilter.overallStatus"] == "RECRUITING"
    assert query["postFilter.geo"] == "distance(40.0,-74.0,25mi)"
    assert query["postFilter.ids"] == "NCT00000003"
    assert query["postFilter.advanced"] == "AREA[StartDate]2022"
    assert query["postFilter.synonyms"] == "BasicSearch:2013558"
    assert query["aggFilters"] == "status:not rec,sex:f"
    assert query["geoDecay"] == "func:linear,scale:100km,offset:10km,decay:0.1"
    assert query["fields"] == "NCTId,BriefTitle"
    assert query["sort"] == "LastUpdatePostDate:desc,@relevance"
    assert query["countTotal"] == "true"
    assert query["pageSize"] == "50"
    assert query["pageToken"] == "token-abc"
    assert query["format"] == "json"
    assert query["markupFormat"] == "markdown"


def test_search_studies_omits_none_params() -> None:
    params = StudiesSearchParams(query_cond="cancer")
    query = params.to_query_params()

    assert "pageToken" not in query
    assert "countTotal" not in query
    assert "filter.overallStatus" not in query
    assert "fields" not in query
    assert query["query.cond"] == "cancer"
    assert query["pageSize"] == "100"


def test_with_phases_builds_advanced_filter() -> None:
    single = StudiesSearchParams.with_phases(["PHASE3"], query_cond="diabetes")
    assert single.filter_advanced == "AREA[Phase]PHASE3"

    multi = StudiesSearchParams.with_phases(
        ["PHASE2", "PHASE3"],
        query_cond="diabetes",
    )
    assert multi.filter_advanced == "AREA[Phase]PHASE2 OR AREA[Phase]PHASE3"


def test_search_studies_returns_studies_and_token() -> None:
    with mock_ctgov_urlopen(
        [
            {
                "json": {
                    "studies": [STUDY_STUB],
                    "nextPageToken": "next-token",
                    "totalCount": 42,
                },
            },
        ],
    ) as get_urls:
        result = _client().search_studies(StudiesSearchParams(query_cond="diabetes"))

    assert len(result.studies) == 1
    assert result.studies[0]["protocolSection"]["identificationModule"]["nctId"] == (
        "NCT00000001"
    )
    assert result.next_page_token == "next-token"
    assert result.total_count == 42

    assert query_param(get_urls()[0], "query.cond") == "diabetes"


def test_search_studies_passes_page_token() -> None:
    with mock_ctgov_urlopen(
        [{"json": {"studies": [STUDY_STUB], "nextPageToken": "page-2"}}],
    ) as get_urls:
        _client().search_studies(
            StudiesSearchParams(query_cond="diabetes", page_token="page-1")
        )

    assert query_param(get_urls()[0], "pageToken") == "page-1"


def test_search_studies_raises_on_400() -> None:
    with (
        mock_ctgov_urlopen(
            [
                {
                    "status_code": 400,
                    "text": "`filter.phase` is unknown parameter",
                },
            ],
        ),
        pytest.raises(CtgovApiError) as exc_info,
    ):
        _client().search_studies(StudiesSearchParams(query_cond="diabetes"))

    assert exc_info.value.status_code == 400
    assert "filter.phase" in exc_info.value.body


def test_search_studies_raises_on_429() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 429, "text": "Too Many Requests"}]),
        pytest.raises(CtgovRateLimitError) as exc_info,
    ):
        _client().search_studies(StudiesSearchParams(query_cond="diabetes"))

    assert exc_info.value.status_code == 429


def test_iter_search_studies_respects_pagination_cap() -> None:
    page_studies = [
        {
            **STUDY_STUB,
            "protocolSection": {"identificationModule": {"nctId": f"NCT{i}"}},
        }
        for i in range(3)
    ]

    with mock_ctgov_urlopen(
        [
            {"json": {"studies": page_studies, "nextPageToken": "page-2"}},
            {"json": {"studies": page_studies, "nextPageToken": "page-3"}},
        ],
    ) as get_urls:
        studies = list(
            _client(pagination_cap=5).iter_search_studies(
                StudiesSearchParams(query_cond="diabetes", page_size=3)
            )
        )

    assert len(studies) == 5
    assert query_param(get_urls()[1], "pageToken") == "page-2"


def test_fetch_search_studies_returns_studies_and_total_count() -> None:
    with mock_ctgov_urlopen(
        [{"json": {"studies": [STUDY_STUB], "totalCount": 99}}],
    ):
        studies, total_count = _client().fetch_search_studies(
            StudiesSearchParams(query_cond="diabetes", count_total=True)
        )

    assert len(studies) == 1
    assert total_count == 99


def test_fetch_search_studies_paginates_until_cap() -> None:
    page_studies = [
        {
            **STUDY_STUB,
            "protocolSection": {"identificationModule": {"nctId": f"NCT{i}"}},
        }
        for i in range(2)
    ]
    with mock_ctgov_urlopen(
        [
            {
                "json": {
                    "studies": page_studies,
                    "nextPageToken": "page-2",
                    "totalCount": 10,
                },
            },
            {"json": {"studies": page_studies, "totalCount": 10}},
        ],
    ):
        studies, total_count = _client(pagination_cap=3).fetch_search_studies(
            StudiesSearchParams(query_cond="diabetes", page_size=2)
        )

    assert len(studies) == 3
    assert total_count == 10


def test_fetch_search_studies_respects_max_studies_override() -> None:
    page_studies = [
        {
            **STUDY_STUB,
            "protocolSection": {"identificationModule": {"nctId": f"NCT{i}"}},
        }
        for i in range(10)
    ]
    with mock_ctgov_urlopen(
        [
            {
                "json": {
                    "studies": page_studies,
                    "nextPageToken": "page-2",
                    "totalCount": 100,
                },
            },
            {"json": {"studies": page_studies, "totalCount": 100}},
        ],
    ) as get_urls:
        studies, total_count = _client(pagination_cap=1000).fetch_search_studies(
            StudiesSearchParams(query_cond="diabetes", page_size=10),
            max_studies=15,
        )

    assert len(studies) == 15
    assert total_count == 100
    assert len(get_urls()) == 2
