import json

import pytest

from app.services.citation_engine import (
    MAX_CITATIONS_PER_DATUM,
    build_citations_for_studies,
    excerpt_start_date,
    make_citation,
)
from app.services.fetch import load_fixture_studies


def test_make_citation_excerpt_is_substring_of_study_json() -> None:
    study = load_fixture_studies("studies_single")[0]
    citation = make_citation(study, excerpt_builder=excerpt_start_date)
    serialized = json.dumps(study, ensure_ascii=False)
    assert citation.nct_id == "NCT05071014"
    assert citation.excerpt in serialized or "2021-09-24" in serialized


def test_build_citations_caps_at_max_per_datum() -> None:
    studies = load_fixture_studies("time_trend_pembrolizumab")
    citations = build_citations_for_studies(
        studies,
        excerpt_builder=excerpt_start_date,
    )
    assert len(citations) == MAX_CITATIONS_PER_DATUM


def test_make_citation_requires_nct_id() -> None:
    with pytest.raises(ValueError, match="missing nctId"):
        make_citation({}, excerpt_builder=lambda _study: "x")
