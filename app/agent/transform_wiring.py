"""Step 5: build TransformContext and run transform_studies."""

from __future__ import annotations

from app.agent.types import APIQueryPlan, FetchResult, Intent
from app.core.schemas.visualization import Visualization
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType, assert_never
from app.infrastructure.ctgov.enums import CtgovEnums
from app.services.transform import transform_studies
from app.services.transform.base import ComparisonArm, TransformContext


def build_transform_context(
    intent: Intent,
    plan: APIQueryPlan,
    fetched: FetchResult,
    viz_type: VisualizationType,
    enums: CtgovEnums,
) -> TransformContext:
    match intent.horizon:
        case Horizon.COMPARISON:
            return TransformContext(
                horizon=Horizon.COMPARISON,
                viz_type=viz_type,
                comparison_arms=tuple(
                    ComparisonArm(label=search.label, studies=arm_studies)
                    for search, arm_studies in zip(
                        plan.searches,
                        fetched.studies_per_search,
                        strict=True,
                    )
                    if search.label is not None
                ),
                bucket_field="phase",
                enums=enums,
            )
        case (
            Horizon.TIME_TREND
            | Horizon.DISTRIBUTION
            | Horizon.GEOGRAPHIC
            | Horizon.NETWORK
        ):
            return TransformContext(
                horizon=intent.horizon,
                viz_type=viz_type,
                studies=fetched.studies_per_search[0],
                bucket_field=intent.bucket_field or "phase",
                time_granularity=intent.time_granularity,
                enums=enums,
            )
        case _ as unreachable:
            assert_never(unreachable)


def run_transform(
    intent: Intent,
    plan: APIQueryPlan,
    fetched: FetchResult,
    viz_type: VisualizationType,
    enums: CtgovEnums,
) -> Visualization:
    context = build_transform_context(intent, plan, fetched, viz_type, enums)
    return transform_studies(context)
