import json

import pytest

from app.services.citation_engine import (
    MAX_CITATIONS_PER_DATUM,
    attach_citations,
    attach_citations_per_bucket,
    build_citations_for_studies,
    excerpt_condition,
    excerpt_country,
    excerpt_enrollment,
    excerpt_intervention,
    excerpt_overall_status,
    excerpt_phase,
    excerpt_sponsor,
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


def test_build_citations_sorts_by_nct_id() -> None:
    studies = load_fixture_studies("time_trend_pembrolizumab")[:3]
    citations = build_citations_for_studies(
        studies,
        excerpt_builder=excerpt_start_date,
    )
    nct_ids = [citation.nct_id for citation in citations]
    assert nct_ids == sorted(nct_ids)


def test_build_citations_skips_invalid_studies() -> None:
    valid = load_fixture_studies("studies_single")[0]
    citations = build_citations_for_studies(
        [{}, valid],
        excerpt_builder=excerpt_start_date,
    )
    assert len(citations) == 1
    assert citations[0].nct_id == "NCT05071014"


def test_attach_citations_skips_invalid_studies() -> None:
    valid = load_fixture_studies("studies_single")[0]
    result = attach_citations(
        {"bucket": [{}, valid]},
        excerpt_builder=excerpt_start_date,
    )
    assert len(result["bucket"]) == 1


def test_attach_citations_per_bucket_uses_bucket_key() -> None:
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT00000001"},
            "contactsLocationsModule": {
                "locations": [
                    {"country": "United States"},
                    {"country": "Canada"},
                ]
            },
        }
    }
    buckets = {"United States": [study], "Canada": [study]}
    result = attach_citations_per_bucket(
        buckets,
        excerpt_builder=lambda s, country: excerpt_country(s, country),
    )
    assert result["United States"][0].excerpt == "United States"
    assert result["Canada"][0].excerpt == "Canada"


@pytest.mark.parametrize(
    ("fixture_name", "builder", "args"),
    [
        ("studies_single", excerpt_start_date, ()),
        ("network_diabetes_sponsor_drug", excerpt_sponsor, ()),
    ],
)
def test_excerpt_builders_return_substrings(fixture_name, builder, args) -> None:
    study = load_fixture_studies(fixture_name)[0]
    excerpt = builder(study, *args) if args else builder(study)
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt in serialized


def test_excerpt_overall_status_returns_substring() -> None:
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT00000001"},
            "statusModule": {"overallStatus": "RECRUITING"},
        }
    }
    excerpt = excerpt_overall_status(study)
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt in serialized


def test_excerpt_enrollment_returns_substring() -> None:
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT00000001"},
            "designModule": {"enrollmentInfo": {"count": 120}},
        }
    }
    excerpt = excerpt_enrollment(study)
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt in serialized


def test_excerpt_phase_uses_phase_code() -> None:
    study = load_fixture_studies("distribution_breast_cancer_phase")[1]
    excerpt = excerpt_phase(study, "PHASE2")
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt == "PHASE2"
    assert excerpt in serialized


def test_excerpt_country_uses_country_name() -> None:
    study = load_fixture_studies("geographic_pembrolizumab_countries")[0]
    excerpt = excerpt_country(study, "United States")
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt in serialized


def test_excerpt_intervention_uses_drug_name() -> None:
    study = load_fixture_studies("network_diabetes_sponsor_drug")[0]
    drug = study["protocolSection"]["armsInterventionsModule"]["interventions"][0][
        "name"
    ]
    excerpt = excerpt_intervention(study, drug)
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt in serialized


def test_excerpt_condition_uses_condition_name() -> None:
    study = load_fixture_studies("network_diabetes_sponsor_drug")[0]
    condition = study["protocolSection"]["conditionsModule"]["conditions"][0]
    excerpt = excerpt_condition(study, condition)
    serialized = json.dumps(study, ensure_ascii=False)
    assert excerpt in serialized


def test_invented_excerpt_raises() -> None:
    study = load_fixture_studies("studies_single")[0]
    with pytest.raises(ValueError, match="Excerpt not found"):
        excerpt_country(study, "Atlantis")
