import pytest

from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.metadata import MetadataParams, StudyMetadata
from tests.infrastructure.ctgov.conftest import (
    mock_ctgov_urlopen,
    query_param,
    url_path,
)

BASE_URL = "https://clinicaltrials.gov/api/v2"

METADATA_FIXTURE = [
    {
        "name": "protocolSection",
        "piece": "ProtocolSection",
        "title": "Protocol Section",
        "sourceType": "STRUCT",
        "type": "ProtocolSection",
        "children": [
            {
                "name": "identificationModule",
                "piece": "IdentificationModule",
                "title": "Identification Module",
                "sourceType": "STRUCT",
                "type": "IdentificationModule",
                "children": [
                    {
                        "name": "nctId",
                        "piece": "NCTId",
                        "title": "NCT Number",
                        "sourceType": "TEXT",
                        "type": "nct",
                    },
                    {
                        "name": "briefTitle",
                        "piece": "BriefTitle",
                        "title": "Brief Title",
                        "sourceType": "TEXT",
                        "type": "text",
                    },
                ],
            }
        ],
    },
    {
        "name": "hasResults",
        "piece": "HasResults",
        "title": "Has Results",
        "sourceType": "FUNC",
        "type": "FUNC",
    },
]


def _client() -> CtgovClient:
    return CtgovClient(BASE_URL, timeout=5.0)


def test_metadata_params_serializes_booleans() -> None:
    assert MetadataParams().to_query_params() == {}

    params = MetadataParams(include_indexed_only=True)
    assert params.to_query_params() == {"includeIndexedOnly": "true"}


def test_metadata_params_both_flags() -> None:
    params = MetadataParams(include_indexed_only=True, include_historic_only=True)
    query = params.to_query_params()

    assert query["includeIndexedOnly"] == "true"
    assert query["includeHistoricOnly"] == "true"


def test_study_metadata_from_api_parses_tree() -> None:
    metadata = StudyMetadata.from_api(METADATA_FIXTURE)

    assert len(metadata.roots) == 2
    assert metadata.roots[0].piece == "ProtocolSection"
    module = metadata.roots[0].children
    assert module is not None
    assert module[0].piece == "IdentificationModule"
    leaves = module[0].children
    assert leaves is not None
    assert leaves[0].piece == "NCTId"
    assert leaves[0].type == "nct"


def test_study_metadata_field_pieces() -> None:
    metadata = StudyMetadata.from_api(METADATA_FIXTURE)

    assert metadata.field_pieces() == ["NCTId", "BriefTitle", "HasResults"]


def test_get_metadata_returns_parsed_tree() -> None:
    with mock_ctgov_urlopen([{"json": METADATA_FIXTURE}]):
        metadata = _client().get_metadata()

    assert metadata.roots[0].piece == "ProtocolSection"
    assert metadata.field_pieces() == ["NCTId", "BriefTitle", "HasResults"]


def test_get_metadata_request_path() -> None:
    with mock_ctgov_urlopen([{"json": METADATA_FIXTURE}]) as get_urls:
        _client().get_metadata()

    assert url_path(get_urls()[0]) == "/api/v2/studies/metadata"


def test_get_metadata_passes_query_params() -> None:
    with mock_ctgov_urlopen([{"json": METADATA_FIXTURE}]) as get_urls:
        _client().get_metadata(MetadataParams(include_indexed_only=True))

    assert query_param(get_urls()[0], "includeIndexedOnly") == "true"


def test_get_metadata_raises_on_404() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 404, "text": "Not found"}]),
        pytest.raises(CtgovApiError) as exc_info,
    ):
        _client().get_metadata()

    assert exc_info.value.status_code == 404


def test_get_metadata_raises_on_429() -> None:
    with (
        mock_ctgov_urlopen([{"status_code": 429, "text": "Too Many Requests"}]),
        pytest.raises(CtgovRateLimitError) as exc_info,
    ):
        _client().get_metadata()

    assert exc_info.value.status_code == 429
