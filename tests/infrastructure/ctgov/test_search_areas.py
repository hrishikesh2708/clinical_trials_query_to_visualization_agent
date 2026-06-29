import pytest

from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.search_areas import StudySearchAreas
from tests.infrastructure.ctgov.conftest import mock_ctgov_urlopen, url_path

BASE_URL = "https://clinicaltrials.gov/api/v2"

SEARCH_AREAS_FIXTURE = [
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
                        "isEnum": False,
                        "isSynonyms": True,
                        "weight": 0.95,
                    }
                ],
            },
            {
                "name": "BasicSearch",
                "uiLabel": "Other terms",
                "param": "term",
                "parts": [
                    {
                        "pieces": ["NCTId", "BriefTitle"],
                        "type": "text",
                        "isEnum": False,
                        "isSynonyms": False,
                        "weight": 1.0,
                    }
                ],
            },
            {
                "name": "InterventionNameSearch",
                "uiLabel": "",
                "param": "",
                "parts": [],
            },
        ],
    }
]


def _client() -> CtgovClient:
    return CtgovClient(BASE_URL, timeout=5.0)


def _search_areas() -> StudySearchAreas:
    return StudySearchAreas.from_api(SEARCH_AREAS_FIXTURE)


def test_study_search_areas_from_api_parses_document() -> None:
    areas = _search_areas()

    assert len(areas.documents) == 1
    assert areas.documents[0].name == "Study"
    assert areas.documents[0].areas[0].name == "ConditionSearch"
    part = areas.documents[0].areas[0].parts[0]
    assert part.pieces == ["Condition"]
    assert part.is_synonyms is True
    assert part.weight == 0.95


def test_areas_with_params_filters_empty_param() -> None:
    with_params = _search_areas().areas_with_params()

    assert len(with_params) == 2
    assert {area.param for area in with_params} == {"cond", "term"}


def test_area_for_param_returns_area() -> None:
    area = _search_areas().area_for_param("cond")

    assert area is not None
    assert area.name == "ConditionSearch"
    assert area.ui_label == "Conditions or disease"


def test_area_for_param_returns_none_for_unknown() -> None:
    assert _search_areas().area_for_param("unknown") is None


def test_query_param_key() -> None:
    assert _search_areas().query_param_key("cond") == "query.cond"


def test_query_param_key_raises_for_unknown() -> None:
    with pytest.raises(KeyError, match="Unknown search area param"):
        _search_areas().query_param_key("unknown")


def test_get_search_areas_returns_parsed() -> None:
    with mock_ctgov_urlopen([{"json": SEARCH_AREAS_FIXTURE}]):
        areas = _client().get_search_areas()

    assert areas.documents[0].name == "Study"
    assert areas.area_for_param("term") is not None


def test_get_search_areas_request_path() -> None:
    with mock_ctgov_urlopen([{"json": SEARCH_AREAS_FIXTURE}]) as get_urls:
        _client().get_search_areas()

    assert url_path(get_urls()[0]) == "/api/v2/studies/search-areas"


def test_get_search_areas_raises_on_404() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 404, "text": "Not found"}]),
        pytest.raises(CtgovApiError) as exc_info,
    ):
        _client().get_search_areas()

    assert exc_info.value.status_code == 404


def test_get_search_areas_raises_on_429() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 429, "text": "Too Many Requests"}]),
        pytest.raises(CtgovRateLimitError) as exc_info,
    ):
        _client().get_search_areas()

    assert exc_info.value.status_code == 429
