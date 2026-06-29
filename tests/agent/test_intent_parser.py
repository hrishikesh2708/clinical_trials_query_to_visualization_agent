"""Tests for intent parser merge and post-validation gates."""

import pytest

from app.agent.exceptions import AgentError
from app.agent.intent_parser import apply_intent_gates, merge_request_filters
from app.agent.types import Intent, ResolvedFilters
from app.core.schemas.request import VisualizeRequest
from app.domain.horizons import Horizon
from app.domain.visualization import TimeGranularity, VisualizationType


def _intent(**updates: object) -> Intent:
    base = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(),
    )
    return base.model_copy(update=updates)


def test_merge_request_filters_request_wins_over_llm() -> None:
    request = VisualizeRequest(
        query="Trials for pembrolizumab",
        drug_name="Pembrolizumab",
    )
    llm_intent = _intent(
        filters=ResolvedFilters(drug_name="Nivolumab"),
    )
    merged = merge_request_filters(request, llm_intent)
    assert merged.filters.drug_name == "Pembrolizumab"


def test_merge_request_filters_keeps_llm_when_request_null() -> None:
    request = VisualizeRequest(query="Breast cancer trials by phase")
    llm_intent = _intent(
        horizon=Horizon.DISTRIBUTION,
        filters=ResolvedFilters(condition="breast cancer"),
    )
    merged = merge_request_filters(request, llm_intent)
    assert merged.filters.condition == "breast cancer"


def test_apply_intent_gates_distribution_defaults_bucket_field() -> None:
    intent = _intent(horizon=Horizon.DISTRIBUTION, bucket_field=None)
    gated = apply_intent_gates(intent)
    assert gated.bucket_field == "phase"


def test_apply_intent_gates_time_trend_clears_bucket_field() -> None:
    intent = _intent(bucket_field="phase")
    gated = apply_intent_gates(intent)
    assert gated.bucket_field is None


def test_apply_intent_gates_geographic_clears_bucket_field() -> None:
    intent = _intent(horizon=Horizon.GEOGRAPHIC, bucket_field="phase")
    gated = apply_intent_gates(intent)
    assert gated.bucket_field is None


def test_apply_intent_gates_comparison_requires_two_arms() -> None:
    intent = _intent(
        horizon=Horizon.COMPARISON,
        comparison_arm_labels=("Pembrolizumab",),
    )
    with pytest.raises(AgentError) as exc_info:
        apply_intent_gates(intent)
    assert exc_info.value.code == "invalid_intent"


def test_apply_intent_gates_clears_incompatible_suggested_viz_type() -> None:
    intent = _intent(suggested_viz_type=VisualizationType.BAR_CHART)
    gated = apply_intent_gates(intent)
    assert gated.suggested_viz_type is None


def test_apply_intent_gates_keeps_compatible_suggested_viz_type() -> None:
    intent = _intent(suggested_viz_type=VisualizationType.TIME_SERIES)
    gated = apply_intent_gates(intent)
    assert gated.suggested_viz_type is VisualizationType.TIME_SERIES


def test_apply_intent_gates_comparison_accepts_two_arms() -> None:
    intent = _intent(
        horizon=Horizon.COMPARISON,
        bucket_field="phase",
        comparison_arm_labels=("Pembrolizumab", "Nivolumab"),
        time_granularity=TimeGranularity.YEAR,
    )
    gated = apply_intent_gates(intent)
    assert gated.comparison_arm_labels == ("Pembrolizumab", "Nivolumab")
