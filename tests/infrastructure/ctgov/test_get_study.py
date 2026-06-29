import pytest

from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.models import StudyGetParams
from tests.infrastructure.ctgov.conftest import (
    mock_ctgov_urlopen,
    query_param,
    url_path,
)

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


def test_get_study_returns_json() -> None:
    with mock_ctgov_urlopen([{"json": STUDY_STUB}]):
        study = _client().get_study("NCT04852770")

    assert study["protocolSection"]["identificationModule"]["nctId"] == "NCT04852770"
    assert study["hasResults"] is False


def test_get_study_puts_nct_id_in_path() -> None:
    with mock_ctgov_urlopen([{"json": STUDY_STUB}]) as get_urls:
        _client().get_study(
            "NCT04852770",
            StudyGetParams(fields=["NCTId", "BriefTitle"]),
        )

    assert url_path(get_urls()[0]) == "/api/v2/studies/NCT04852770"
    assert query_param(get_urls()[0], "fields") == "NCTId,BriefTitle"


def test_get_study_raises_on_invalid_nct_id() -> None:
    with pytest.raises(ValueError, match="Invalid NCT ID"):
        _client().get_study("INVALID")


def test_get_study_raises_on_404() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 404, "text": "Study not found"}]),
        pytest.raises(CtgovApiError) as exc_info,
    ):
        _client().get_study("NCT04852770")

    assert exc_info.value.status_code == 404


def test_get_study_raises_on_429() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 429, "text": "Too Many Requests"}]),
        pytest.raises(CtgovRateLimitError) as exc_info,
    ):
        _client().get_study("NCT04852770")

    assert exc_info.value.status_code == 429


def test_get_study_follows_redirect() -> None:
    """urllib follows redirects internally; client sees the final JSON response."""
    with mock_ctgov_urlopen([{"json": STUDY_STUB}]):
        study = _client().get_study("NCT00000001")

    assert study["protocolSection"]["identificationModule"]["nctId"] == "NCT04852770"
