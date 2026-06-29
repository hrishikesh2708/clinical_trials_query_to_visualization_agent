"""Pipeline step input/output contracts for the visualize agent."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.horizons import Horizon
from app.domain.visualization import TimeGranularity, VisualizationType
from app.infrastructure.ctgov.models import StudiesSearchParams

BucketField = Literal["phase", "overall_status", "enrollment"]


class ResolvedFilters(BaseModel):
    """Echo of structured filters after merging request + LLM inference."""

    drug_name: str | None = None
    condition: str | None = None
    trial_phase: str | None = None
    sponsor: str | None = None
    country: str | None = None
    start_year: int | None = Field(
        default=None,
        description=(
            "Inclusive lower bound when query says since/from/after YYYY; else null."
        ),
    )
    end_year: int | None = Field(
        default=None,
        description=(
            "Inclusive upper bound when query says before/until YYYY "
            "or between X and Y; else null."
        ),
    )


class Intent(BaseModel):
    horizon: Horizon
    filters: ResolvedFilters
    bucket_field: BucketField | None = None
    time_granularity: TimeGranularity = TimeGranularity.YEAR
    comparison_arm_labels: tuple[str, ...] = ()
    suggested_viz_type: VisualizationType | None = None
    assumptions: list[str] = Field(default_factory=list)


class SearchParamsDraft(BaseModel):
    query_cond: str | None = None
    query_term: str | None = None
    query_locn: str | None = None
    query_intr: str | None = None
    query_spons: str | None = None
    query_lead: str | None = None
    filter_overall_status: list[str] | None = None
    filter_geo: str | None = None
    filter_advanced: str | None = None


class PlannedSearchDraft(BaseModel):
    label: str | None = None
    params: SearchParamsDraft


class QueryPlanDraft(BaseModel):
    searches: list[PlannedSearchDraft]
    planning_notes: list[str] = Field(default_factory=list)


class PlannedSearch(BaseModel):
    label: str | None = None
    params: StudiesSearchParams
    fields: list[str]


class APIQueryPlan(BaseModel):
    horizon: Horizon
    searches: list[PlannedSearch]
    normalization_notes: list[str] = Field(default_factory=list)


class SearchPreview(BaseModel):
    label: str | None
    studies_fetched: int
    total_count: int | None


class FetchPreview(BaseModel):
    searches: list[SearchPreview]
    allowed_viz_types: list[VisualizationType]


class VizSelection(BaseModel):
    viz_type: VisualizationType


class ResponseNarrative(BaseModel):
    title: str
    interpretation_notes: str | None = None
    additional_assumptions: list[str] = Field(default_factory=list)


class FetchResult(BaseModel):
    """Studies per search plus preview metadata from Step 3."""

    studies_per_search: list[list[dict[str, Any]]]
    preview: FetchPreview
