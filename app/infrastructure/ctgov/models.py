from typing import Any, Literal

from pydantic import BaseModel, Field


def _join_list(values: list[str]) -> str:
    return ",".join(values)


def _phase_advanced_expression(phases: list[str]) -> str:
    clauses = [f"AREA[Phase]{phase}" for phase in phases]
    if len(clauses) == 1:
        return clauses[0]
    return " OR ".join(clauses)


class StudiesSearchParams(BaseModel):
    format: Literal["json", "csv"] = "json"
    markup_format: Literal["markdown", "legacy"] = "markdown"
    query_cond: str | None = None
    query_term: str | None = None
    query_locn: str | None = None
    query_titles: str | None = None
    query_intr: str | None = None
    query_outc: str | None = None
    query_spons: str | None = None
    query_lead: str | None = None
    query_id: str | None = None
    query_patient: str | None = None
    filter_overall_status: list[str] | None = None
    filter_geo: str | None = None
    filter_ids: list[str] | None = None
    filter_advanced: str | None = None
    filter_synonyms: list[str] | None = None
    post_filter_overall_status: list[str] | None = None
    post_filter_geo: str | None = None
    post_filter_ids: list[str] | None = None
    post_filter_advanced: str | None = None
    post_filter_synonyms: list[str] | None = None
    agg_filters: str | None = None
    geo_decay: str | None = None
    fields: list[str] | None = None
    sort: list[str] | None = None
    count_total: bool = False
    page_size: int = Field(default=100, ge=0, le=1000)
    page_token: str | None = None

    @classmethod
    def with_phases(cls, phases: list[str], **kwargs: Any) -> "StudiesSearchParams":
        return cls(filter_advanced=_phase_advanced_expression(phases), **kwargs)

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {
            "format": self.format,
            "markupFormat": self.markup_format,
            "pageSize": str(self.page_size),
        }

        if self.count_total:
            params["countTotal"] = "true"

        if self.page_token is not None:
            params["pageToken"] = self.page_token

        string_fields = {
            "query.cond": self.query_cond,
            "query.term": self.query_term,
            "query.locn": self.query_locn,
            "query.titles": self.query_titles,
            "query.intr": self.query_intr,
            "query.outc": self.query_outc,
            "query.spons": self.query_spons,
            "query.lead": self.query_lead,
            "query.id": self.query_id,
            "query.patient": self.query_patient,
            "filter.geo": self.filter_geo,
            "filter.advanced": self.filter_advanced,
            "postFilter.geo": self.post_filter_geo,
            "postFilter.advanced": self.post_filter_advanced,
            "aggFilters": self.agg_filters,
            "geoDecay": self.geo_decay,
        }
        for key, value in string_fields.items():
            if value is not None:
                params[key] = value

        list_fields = {
            "filter.overallStatus": self.filter_overall_status,
            "filter.ids": self.filter_ids,
            "filter.synonyms": self.filter_synonyms,
            "postFilter.overallStatus": self.post_filter_overall_status,
            "postFilter.ids": self.post_filter_ids,
            "postFilter.synonyms": self.post_filter_synonyms,
            "fields": self.fields,
            "sort": self.sort,
        }
        for key, value in list_fields.items():
            if value:
                params[key] = _join_list(value)

        return params


class StudiesSearchResult(BaseModel):
    studies: list[dict[str, Any]]
    next_page_token: str | None
    total_count: int | None = None
