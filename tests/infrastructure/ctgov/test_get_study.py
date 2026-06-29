import pytest

from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.models import StudyGetParams

BASE_URL = "https://clinicaltrials.gov/api/v2"
STUDY_STUB = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT04852770",
            "briefTitle": "Test Study",
        }
    },
    "hasResults": False,
}


def _client() -> CtgovClient:
    return CtgovClient(BASE_URL, timeout=5.0)


def test_study_get_params_serializes_query_string() -> None:
    params = StudyGetParams(
        format="fhir.json",
        markup_format="legacy",
        fields=["NCTId", "BriefTitle", "Reference"],
    )
    query = params.to_query_params()

    assert query["format"] == "fhir.json"
    assert query["markupFormat"] == "legacy"
    assert query["fields"] == "NCTId,BriefTitle,Reference"


def test_study_get_params_omits_empty_fields() -> None:
    params = StudyGetParams()
    query = params.to_query_params()

    assert "fields" not in query
    assert query["format"] == "json"
    assert query["markupFormat"] == "markdown"


def test_get_study_returns_json(httpx_mock) -> None:
    httpx_mock.add_response(json=STUDY_STUB)

    study = _client().get_study("NCT04852770")

    assert study["protocolSection"]["identificationModule"]["nctId"] == "NCT04852770"
    assert study["hasResults"] is False


def test_get_study_puts_nct_id_in_path(httpx_mock) -> None:
    httpx_mock.add_response(json=STUDY_STUB)

    _client().get_study(
        "NCT04852770",
        StudyGetParams(fields=["NCTId", "BriefTitle"]),
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.path == "/api/v2/studies/NCT04852770"
    assert request.url.params["fields"] == "NCTId,BriefTitle"


def test_get_study_raises_on_invalid_nct_id() -> None:
    with pytest.raises(ValueError, match="Invalid NCT ID"):
        _client().get_study("INVALID")


def test_get_study_raises_on_404(httpx_mock) -> None:
    httpx_mock.add_response(status_code=404, text="Study not found")

    with pytest.raises(CtgovApiError) as exc_info:
        _client().get_study("NCT04852770")

    assert exc_info.value.status_code == 404


def test_get_study_raises_on_429(httpx_mock) -> None:
    httpx_mock.add_response(status_code=429, text="Too Many Requests")

    with pytest.raises(CtgovRateLimitError) as exc_info:
        _client().get_study("NCT04852770")

    assert exc_info.value.status_code == 429


def test_get_study_follows_redirect(httpx_mock) -> None:
    httpx_mock.add_response(
        status_code=301,
        headers={
            "Location": (
                f"{BASE_URL}/studies/NCT04852770"
                "?format=json&markupFormat=markdown"
            ),
        },
    )
    httpx_mock.add_response(json=STUDY_STUB)

    study = _client().get_study("NCT00000001")

    assert study["protocolSection"]["identificationModule"]["nctId"] == "NCT04852770"
    assert len(httpx_mock.get_requests()) == 2
