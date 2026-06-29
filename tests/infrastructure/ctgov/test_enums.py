import pytest

from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.enums import CtgovEnums, CtgovEnumsLoader
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError

BASE_URL = "https://clinicaltrials.gov/api/v2"

ENUMS_FIXTURE = [
    {
        "type": "Phase",
        "pieces": ["Phase"],
        "values": [
            {"value": "NA", "legacyValue": "Not Applicable"},
            {"value": "EARLY_PHASE1", "legacyValue": "Early Phase 1"},
            {"value": "PHASE1", "legacyValue": "Phase 1"},
            {"value": "PHASE2", "legacyValue": "Phase 2"},
            {"value": "PHASE3", "legacyValue": "Phase 3"},
            {"value": "PHASE4", "legacyValue": "Phase 4"},
        ],
    },
    {
        "type": "Status",
        "pieces": ["OverallStatus"],
        "values": [
            {"value": "RECRUITING", "legacyValue": "Recruiting"},
            {"value": "COMPLETED", "legacyValue": "Completed"},
            {"value": "TERMINATED", "legacyValue": "Terminated"},
        ],
    },
]


def _client() -> CtgovClient:
    return CtgovClient(BASE_URL, timeout=5.0)


def _enums() -> CtgovEnums:
    return CtgovEnums.from_api(ENUMS_FIXTURE)


def test_ctgov_enums_from_api_parses_types() -> None:
    enums = _enums()

    assert len(enums.enums) == 2
    assert enums.enums[0].type == "Phase"
    assert enums.enums[0].values[2].value == "PHASE1"
    assert enums.enums[0].values[2].legacy_value == "Phase 1"


def test_validate_phase_accepts_canonical_value() -> None:
    assert _enums().validate_phase("PHASE3") == "PHASE3"


def test_validate_phase_accepts_legacy_value() -> None:
    assert _enums().validate_phase("Phase 3") == "PHASE3"


def test_validate_phase_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="Invalid Phase value"):
        _enums().validate_phase("PHASE99")


def test_validate_overall_status_accepts_canonical_value() -> None:
    assert _enums().validate_overall_status("RECRUITING") == "RECRUITING"


def test_validate_overall_status_accepts_legacy_value() -> None:
    assert _enums().validate_overall_status("Recruiting") == "RECRUITING"


def test_label_for_returns_legacy_display_value() -> None:
    assert _enums().label_for("Phase", "PHASE3") == "Phase 3"
    assert _enums().label_for("Phase", "Phase 3") == "Phase 3"
    assert _enums().label_for("Status", "RECRUITING") == "Recruiting"


def test_validate_overall_status_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="Invalid Status value"):
        _enums().validate_overall_status("INVALID")


def test_fetch_enums_returns_parsed_response(httpx_mock) -> None:
    httpx_mock.add_response(json=ENUMS_FIXTURE)

    data = _client().fetch_enums()

    assert len(data) == 2
    assert data[0]["type"] == "Phase"
    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.path == "/api/v2/studies/enums"


def test_enums_loader_caches_after_first_load(httpx_mock) -> None:
    httpx_mock.add_response(json=ENUMS_FIXTURE)

    loader = CtgovEnumsLoader(_client())
    first = loader.load()
    second = loader.load()

    assert first is second
    assert len(httpx_mock.get_requests()) == 1


def test_enums_loader_force_refresh_fetches_again(httpx_mock) -> None:
    httpx_mock.add_response(json=ENUMS_FIXTURE)
    httpx_mock.add_response(json=ENUMS_FIXTURE)

    loader = CtgovEnumsLoader(_client())
    first = loader.load()
    second = loader.load(force_refresh=True)

    assert first is not second
    assert len(httpx_mock.get_requests()) == 2


def test_enums_loader_validate_phase_delegates_to_cache(httpx_mock) -> None:
    httpx_mock.add_response(json=ENUMS_FIXTURE)

    loader = CtgovEnumsLoader(_client())

    assert loader.validate_phase("Phase 2") == "PHASE2"
    assert len(httpx_mock.get_requests()) == 1


def test_fetch_enums_raises_on_429(httpx_mock) -> None:
    httpx_mock.add_response(status_code=429, text="Too Many Requests")

    with pytest.raises(CtgovRateLimitError):
        _client().fetch_enums()


def test_fetch_enums_raises_on_500(httpx_mock) -> None:
    httpx_mock.add_response(status_code=500, text="Server error")

    with pytest.raises(CtgovApiError) as exc_info:
        _client().fetch_enums()

    assert exc_info.value.status_code == 500
