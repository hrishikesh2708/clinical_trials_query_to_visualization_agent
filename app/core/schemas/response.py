from pydantic import BaseModel, Field

from app.core.schemas.visualization import Visualization
from app.domain.visualization import DataSource, TimeGranularity


class AppliedFilters(BaseModel):
    """Echo of structured filters used for the query (resolved values)."""

    drug_name: str | None = None
    condition: str | None = None
    trial_phase: str | None = None
    sponsor: str | None = None
    country: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class ResponseMeta(BaseModel):
    source: DataSource = DataSource.CLINICALTRIALS_GOV
    filters: AppliedFilters
    assumptions: list[str] = Field(default_factory=list)
    time_granularity: TimeGranularity | None = None
    units: dict[str, str] | None = None
    total_studies_fetched: int = Field(..., ge=0)
    interpretation_notes: str | None = None


class VisualizeResponse(BaseModel):
    visualization: Visualization
    meta: ResponseMeta
