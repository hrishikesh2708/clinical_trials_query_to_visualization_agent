import pytest
from pydantic import ValidationError

from app.core.schemas.request import VisualizeRequest


def test_minimal_request_accepts_query_only() -> None:
    request = VisualizeRequest(query="How many Phase 3 trials are recruiting?")
    assert request.query == "How many Phase 3 trials are recruiting?"
    assert request.drug_name is None


def test_full_illustrative_request() -> None:
    payload = {
        "query": (
            "How has the number of trials for pembrolizumab "
            "changed per year since 2015?"
        ),
        "drug_name": "Pembrolizumab",
        "condition": None,
        "trial_phase": None,
        "sponsor": None,
        "country": None,
        "start_year": 2015,
        "end_year": None,
    }
    request = VisualizeRequest.model_validate(payload)
    assert request.drug_name == "Pembrolizumab"
    assert request.start_year == 2015
    assert request.end_year is None


def test_request_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        VisualizeRequest(query="")


def test_request_rejects_start_year_after_end_year() -> None:
    with pytest.raises(ValidationError, match="start_year must be less than or equal"):
        VisualizeRequest(
            query="Trials over time",
            start_year=2020,
            end_year=2015,
        )


def test_request_round_trip_json() -> None:
    original = VisualizeRequest(
        query="Melanoma trials in the US",
        condition="Melanoma",
        country="United States",
        start_year=2010,
        end_year=2020,
    )
    restored = VisualizeRequest.model_validate_json(original.model_dump_json())
    assert restored == original
