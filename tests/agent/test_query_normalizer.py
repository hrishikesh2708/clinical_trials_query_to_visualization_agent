"""Tests for query plan normalization."""

import pytest

from app.agent.exceptions import AgentError
from app.agent.query_normalizer import normalize_query_plan, resolve_fields
from app.agent.types import (
    Intent,
    PlannedSearchDraft,
    QueryPlanDraft,
    ResolvedFilters,
    SearchParamsDraft,
)
from app.domain.horizons import Horizon
from tests.agent.conftest import enums_from_fixture


def _intent(**updates: object) -> Intent:
    base = Intent(
        horizon=Horizon.DISTRIBUTION,
        filters=ResolvedFilters(),
        bucket_field="phase",
    )
    return base.model_copy(update=updates)


def test_resolve_fields_distribution_phase_bucket() -> None:
    intent = _intent(bucket_field="phase")
    assert resolve_fields(intent) == ["NCTId", "Phase"]


def test_resolve_fields_distribution_enrollment_bucket() -> None:
    intent = _intent(bucket_field="enrollment")
    assert resolve_fields(intent) == ["NCTId", "Phase", "EnrollmentCount"]


def test_normalize_distribution_phase_bucket() -> None:
    intent = _intent()
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(query_cond="breast cancer"),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert plan.horizon is Horizon.DISTRIBUTION
    assert len(plan.searches) == 1
    search = plan.searches[0]
    assert search.fields == ["NCTId", "Phase"]
    assert search.params.query_cond == "breast cancer"
    assert search.params.count_total is True
    assert search.params.page_size == 100
    assert (
        "Set count_total=true and fields from horizon spec."
        in plan.normalization_notes
    )


def test_normalize_time_trend_injects_start_year() -> None:
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(query_intr="Pembrolizumab"),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert (
        plan.searches[0].params.filter_advanced
        == "AREA[StartDate]RANGE[2015-01-01,MAX]"
    )
    assert "Injected start/end year filter from intent." in plan.normalization_notes


def test_normalize_injects_drug_name_when_draft_omits_query_intr() -> None:
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab"),
    )
    draft = QueryPlanDraft(
        searches=[PlannedSearchDraft(params=SearchParamsDraft())]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert plan.searches[0].params.query_intr == "Pembrolizumab"
    assert "Injected query_intr from intent drug_name." in plan.normalization_notes


def test_normalize_comparison_two_arms() -> None:
    intent = Intent(
        horizon=Horizon.COMPARISON,
        filters=ResolvedFilters(),
        comparison_arm_labels=("Pembrolizumab", "Nivolumab"),
        bucket_field="phase",
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                label="arm-a",
                params=SearchParamsDraft(query_intr="Pembrolizumab"),
            ),
            PlannedSearchDraft(
                label="arm-b",
                params=SearchParamsDraft(query_intr="Nivolumab"),
            ),
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert len(plan.searches) == 2
    assert plan.searches[0].label == "Pembrolizumab"
    assert plan.searches[1].label == "Nivolumab"
    assert plan.searches[0].params.query_intr == "Pembrolizumab"
    assert plan.searches[0].fields == ["NCTId", "Phase", "InterventionName"]


def test_normalize_geographic_country_sets_query_locn_and_clears_filter_geo() -> None:
    intent = Intent(
        horizon=Horizon.GEOGRAPHIC,
        filters=ResolvedFilters(drug_name="Pembrolizumab", country="Germany"),
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(
                    query_intr="Pembrolizumab",
                    filter_geo="Germany",
                ),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    search = plan.searches[0].params
    assert search.query_locn == "Germany"
    assert search.filter_geo is None
    assert "Cleared non-proximity filter_geo" in " ".join(plan.normalization_notes)


def test_normalize_unknown_phase_raises_invalid_query_plan() -> None:
    intent = _intent(filters=ResolvedFilters(trial_phase="PHASE99"))
    draft = QueryPlanDraft(
        searches=[PlannedSearchDraft(params=SearchParamsDraft(query_cond="cancer"))]
    )
    with pytest.raises(AgentError) as exc_info:
        normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert exc_info.value.code == "invalid_query_plan"


def test_normalize_comparison_count_mismatch_raises_invalid_query_plan() -> None:
    intent = Intent(
        horizon=Horizon.COMPARISON,
        filters=ResolvedFilters(),
        comparison_arm_labels=("A", "B"),
    )
    draft = QueryPlanDraft(
        searches=[PlannedSearchDraft(params=SearchParamsDraft(query_intr="A"))]
    )
    with pytest.raises(AgentError) as exc_info:
        normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert exc_info.value.code == "invalid_query_plan"
    assert "requires 2 searches" in exc_info.value.message


def test_normalize_time_trend_strips_unauthorized_start_date() -> None:
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab"),
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(
                    query_intr="Pembrolizumab",
                    filter_advanced="AREA[StartDate]2015",
                ),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert plan.searches[0].params.filter_advanced is None
    assert (
        "Removed unauthorized StartDate filter; no date range in intent."
        in plan.normalization_notes
    )


def test_normalize_distribution_strips_unauthorized_phase_filter() -> None:
    intent = _intent()
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(
                    query_cond="breast cancer",
                    filter_advanced="AREA[Phase]PHASE3",
                ),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert plan.searches[0].params.filter_advanced is None
    assert (
        "Removed unauthorized Phase filter; no trial_phase in intent."
        in plan.normalization_notes
    )


def test_normalize_keeps_start_date_strips_unauthorized_phase() -> None:
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(
                    query_intr="Pembrolizumab",
                    filter_advanced="AREA[Phase]PHASE2 AND AREA[StartDate]2015",
                ),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert (
        plan.searches[0].params.filter_advanced
        == "AREA[StartDate]RANGE[2015-01-01,MAX]"
    )
    assert (
        "Removed unauthorized Phase filter; no trial_phase in intent."
        in plan.normalization_notes
    )


def test_normalize_time_trend_replaces_malformed_llm_start_date_range() -> None:
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(
            drug_name="Pembrolizumab",
            start_year=2015,
            end_year=2018,
        ),
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(
                    query_intr="Pembrolizumab",
                    filter_advanced="AREA[StartDate]RANGE[2015-2018]",
                ),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert (
        plan.searches[0].params.filter_advanced
        == "AREA[StartDate]RANGE[2015-01-01,2018-12-31]"
    )
    assert (
        "Replaced LLM StartDate filter with canonical API format from intent."
        in plan.normalization_notes
    )


def test_normalize_time_trend_replaces_natural_language_llm_start_date_range() -> None:
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(
            drug_name="Pembrolizumab",
            start_year=2015,
            end_year=2018,
        ),
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(
                    query_intr="Pembrolizumab",
                    filter_advanced="AREA[StartDate]RANGE[2015 to 2018]",
                ),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert (
        plan.searches[0].params.filter_advanced
        == "AREA[StartDate]RANGE[2015-01-01,2018-12-31]"
    )


def test_normalize_injects_phase_when_trial_phase_in_intent() -> None:
    intent = _intent(filters=ResolvedFilters(trial_phase="Phase 3"))
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(query_cond="breast cancer"),
            )
        ]
    )
    plan = normalize_query_plan(intent, draft, enums=enums_from_fixture())
    assert plan.searches[0].params.filter_advanced == "AREA[Phase]PHASE3"
    assert (
        "Injected phase filter AREA[Phase]PHASE3 from intent."
        in plan.normalization_notes
    )
