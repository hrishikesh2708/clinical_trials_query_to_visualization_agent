"""Tests for agent pipeline type contracts."""

from app.agent.types import APIQueryPlan, Intent
from app.domain.horizons import Horizon
from app.domain.visualization import TimeGranularity, VisualizationType


def test_intent_time_trend_example_from_spec() -> None:
    payload = {
        "horizon": "time_trend",
        "filters": {
            "drug_name": "Pembrolizumab",
            "condition": None,
            "trial_phase": None,
            "sponsor": None,
            "country": None,
            "start_year": 2015,
            "end_year": None,
        },
        "bucket_field": None,
        "time_granularity": "year",
        "comparison_arm_labels": [],
        "suggested_viz_type": "time_series",
        "assumptions": [
            (
                "Using study start date; preferring ACTUAL over ESTIMATED "
                "per horizon_matrix."
            ),
        ],
    }
    intent = Intent.model_validate(payload)
    assert intent.horizon is Horizon.TIME_TREND
    assert intent.filters.drug_name == "Pembrolizumab"
    assert intent.filters.start_year == 2015
    assert intent.bucket_field is None
    assert intent.time_granularity is TimeGranularity.YEAR
    assert intent.comparison_arm_labels == ()
    assert intent.suggested_viz_type is VisualizationType.TIME_SERIES
    assert len(intent.assumptions) == 1


def test_intent_comparison_example_from_spec() -> None:
    payload = {
        "horizon": "comparison",
        "filters": {
            "drug_name": None,
            "condition": None,
            "trial_phase": None,
            "sponsor": None,
            "country": None,
            "start_year": None,
            "end_year": None,
        },
        "bucket_field": "phase",
        "time_granularity": "year",
        "comparison_arm_labels": ["Pembrolizumab", "Nivolumab"],
        "suggested_viz_type": "grouped_bar_chart",
        "assumptions": [
            "Comparing intervention cohorts via separate query.intr searches."
        ],
    }
    intent = Intent.model_validate(payload)
    assert intent.horizon is Horizon.COMPARISON
    assert intent.bucket_field == "phase"
    assert intent.comparison_arm_labels == ("Pembrolizumab", "Nivolumab")
    assert intent.suggested_viz_type is VisualizationType.GROUPED_BAR_CHART


def test_api_query_plan_distribution_example_from_spec() -> None:
    payload = {
        "horizon": "distribution",
        "searches": [
            {
                "label": None,
                "params": {
                    "format": "json",
                    "query_cond": "breast cancer",
                    "count_total": True,
                    "page_size": 100,
                    "fields": ["NCTId", "Phase"],
                },
                "fields": ["NCTId", "Phase"],
            }
        ],
        "normalization_notes": ["Set count_total=true and fields from horizon spec."],
    }
    plan = APIQueryPlan.model_validate(payload)
    assert plan.horizon is Horizon.DISTRIBUTION
    assert len(plan.searches) == 1
    assert plan.searches[0].params.query_cond == "breast cancer"
    assert plan.searches[0].params.count_total is True
    assert plan.searches[0].fields == ["NCTId", "Phase"]
    assert plan.normalization_notes == [
        "Set count_total=true and fields from horizon spec."
    ]


def test_api_query_plan_comparison_example_from_spec() -> None:
    payload = {
        "horizon": "comparison",
        "searches": [
            {
                "label": "Pembrolizumab",
                "params": {
                    "query_intr": "Pembrolizumab",
                    "count_total": True,
                    "page_size": 100,
                    "fields": ["NCTId", "Phase", "InterventionName"],
                },
                "fields": ["NCTId", "Phase", "InterventionName"],
            },
            {
                "label": "Nivolumab",
                "params": {
                    "query_intr": "Nivolumab",
                    "count_total": True,
                    "page_size": 100,
                    "fields": ["NCTId", "Phase", "InterventionName"],
                },
                "fields": ["NCTId", "Phase", "InterventionName"],
            },
        ],
        "normalization_notes": [],
    }
    plan = APIQueryPlan.model_validate(payload)
    assert plan.horizon is Horizon.COMPARISON
    assert len(plan.searches) == 2
    assert plan.searches[0].label == "Pembrolizumab"
    assert plan.searches[1].label == "Nivolumab"
    assert plan.searches[0].params.query_intr == "Pembrolizumab"
    assert plan.searches[1].params.query_intr == "Nivolumab"
