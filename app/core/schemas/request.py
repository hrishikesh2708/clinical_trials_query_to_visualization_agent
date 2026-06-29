"""Request schema for the visualize endpoint.

Validation rules:
- ``query`` is required and must be non-empty.
- All structured filter fields are optional.
- ``start_year`` and ``end_year`` must be between 1900 and 2100 when provided.
- When both years are set, ``start_year`` must be less than or equal to ``end_year``.
- ``trial_phase`` is free-text here; ctgov enum validation is deferred to Stage 6.

Example::

    {
        "query": (
            "How has the number of trials for pembrolizumab "
            "changed per year since 2015?"
        ),
        "drug_name": "Pembrolizumab",
        "condition": null,
        "trial_phase": null,
        "sponsor": null,
        "country": null,
        "start_year": 2015,
        "end_year": null
    }
"""

from pydantic import BaseModel, Field, model_validator


class VisualizeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    drug_name: str | None = None
    condition: str | None = None
    trial_phase: str | None = None
    sponsor: str | None = None
    country: str | None = None
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)

    @model_validator(mode="after")
    def validate_year_range(self) -> "VisualizeRequest":
        if self.start_year is not None and self.end_year is not None:
            if self.start_year > self.end_year:
                raise ValueError("start_year must be less than or equal to end_year")
        return self
