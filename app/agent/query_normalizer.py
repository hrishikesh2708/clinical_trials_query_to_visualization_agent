"""Step 2 Python normalizer: QueryPlanDraft → APIQueryPlan."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from app.agent.advanced_filter_validator import (
    find_invalid_start_date_clauses,
    is_start_date_clause,
)
from app.agent.exceptions import AgentError
from app.agent.types import (
    APIQueryPlan,
    Intent,
    PlannedSearch,
    PlannedSearchDraft,
    QueryPlanDraft,
    SearchParamsDraft,
)
from app.domain.horizons import Horizon, horizon_spec
from app.domain.visualization import assert_never
from app.infrastructure.ctgov.enums import CtgovEnums
from app.infrastructure.ctgov.models import StudiesSearchParams

_GEO_DISTANCE_PATTERN = re.compile(r"^distance\s*\(", re.IGNORECASE)
_PHASE_TOKEN_PATTERN = re.compile(r"AREA\[Phase\]([A-Z0-9_]+)")
_AND_SPLIT_PATTERN = re.compile(r"\s+AND\s+", re.IGNORECASE)
_PHASE_CLAUSE_PATTERN = re.compile(
    r"^AREA\[Phase\][A-Z0-9_]+(?:\s+OR\s+AREA\[Phase\][A-Z0-9_]+)*$",
    re.IGNORECASE,
)


def resolve_fields(intent: Intent) -> list[str]:
    fields = list(horizon_spec(intent.horizon).fields_pieces)
    if intent.horizon is Horizon.DISTRIBUTION:
        bucket_field = intent.bucket_field or "phase"
        if bucket_field == "overall_status" and "OverallStatus" not in fields:
            fields.append("OverallStatus")
        elif bucket_field == "enrollment" and "EnrollmentCount" not in fields:
            fields.append("EnrollmentCount")
    return fields


def _date_advanced_clause(start_year: int | None, end_year: int | None) -> str | None:
    if start_year is not None and end_year is not None:
        return f"AREA[StartDate]RANGE[{start_year}-01-01,{end_year}-12-31]"
    if start_year is not None:
        return f"AREA[StartDate]RANGE[{start_year}-01-01,MAX]"
    if end_year is not None:
        return f"AREA[StartDate]RANGE[MIN,{end_year}-12-31]"
    return None


def _merge_advanced_clauses(*clauses: str | None) -> str | None:
    present = [clause.strip() for clause in clauses if clause and clause.strip()]
    if not present:
        return None
    return " AND ".join(present)


def _validate_phase_tokens(expression: str | None, enums: CtgovEnums) -> None:
    if not expression:
        return
    for match in _PHASE_TOKEN_PATTERN.finditer(expression):
        enums.validate_phase(match.group(1))


def _authorized_date_filter(intent: Intent) -> bool:
    return (
        intent.filters.start_year is not None or intent.filters.end_year is not None
    )


def _authorized_phase_filter(intent: Intent) -> bool:
    return intent.filters.trial_phase is not None


def _split_and_clauses(expression: str) -> list[str]:
    return [
        clause.strip()
        for clause in _AND_SPLIT_PATTERN.split(expression.strip())
        if clause.strip()
    ]


def _filter_and_clauses(
    expression: str | None,
    *,
    drop_if: Callable[[str], bool],
) -> tuple[str | None, bool]:
    if not expression or not expression.strip():
        return expression, False
    clauses = _split_and_clauses(expression)
    kept = [clause for clause in clauses if not drop_if(clause)]
    if len(kept) == len(clauses):
        return expression, False
    if not kept:
        return None, True
    return " AND ".join(kept), True


def _strip_start_date_clauses(
    expression: str | None,
) -> tuple[str | None, bool]:
    return _filter_and_clauses(expression, drop_if=is_start_date_clause)


def _strip_unauthorized_advanced_filters(
    intent: Intent,
    existing: str | None,
) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    expression = existing

    if not _authorized_phase_filter(intent):
        expression, changed = _filter_and_clauses(
            expression,
            drop_if=lambda clause: bool(_PHASE_CLAUSE_PATTERN.match(clause)),
        )
        if changed:
            notes.append(
                "Removed unauthorized Phase filter; no trial_phase in intent."
            )

    return expression, notes


def _validate_start_date_clauses(expression: str | None) -> None:
    invalid = find_invalid_start_date_clauses(expression)
    if invalid:
        raise AgentError(
            "invalid_query_plan",
            (
                f"Invalid StartDate advanced filter {invalid[0]!r}; "
                "use AREA[StartDate]RANGE[YYYY-MM-DD,YYYY-MM-DD], "
                "RANGE[YYYY-MM-DD,MAX], or RANGE[MIN,YYYY-MM-DD]."
            ),
        )


def build_advanced_filters(
    intent: Intent,
    enums: CtgovEnums,
    existing: str | None,
) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    injected_clauses: list[str] = []

    existing, strip_notes = _strip_unauthorized_advanced_filters(intent, existing)
    notes.extend(strip_notes)

    replaced_llm_start_date = False
    if _authorized_date_filter(intent):
        existing, replaced_llm_start_date = _strip_start_date_clauses(existing)
        if replaced_llm_start_date:
            notes.append(
                "Replaced LLM StartDate filter with canonical API format from intent."
            )
    else:
        existing, removed_unauthorized = _strip_start_date_clauses(existing)
        if removed_unauthorized:
            notes.append(
                "Removed unauthorized StartDate filter; no date range in intent."
            )

    if intent.filters.trial_phase and (
        existing is None or intent.filters.trial_phase not in (existing or "")
    ):
        try:
            phase_code = enums.validate_phase(intent.filters.trial_phase)
        except ValueError as exc:
            raise AgentError("invalid_query_plan", str(exc)) from exc
        injected_clauses.append(f"AREA[Phase]{phase_code}")
        notes.append(f"Injected phase filter AREA[Phase]{phase_code} from intent.")

    date_clause = _date_advanced_clause(
        intent.filters.start_year,
        intent.filters.end_year,
    )
    if date_clause:
        injected_clauses.append(date_clause)
        if not replaced_llm_start_date:
            notes.append("Injected start/end year filter from intent.")

    merged = _merge_advanced_clauses(existing, *injected_clauses)
    try:
        if merged and merged != existing:
            _validate_phase_tokens(merged, enums)
        elif existing:
            _validate_phase_tokens(existing, enums)
    except ValueError as exc:
        raise AgentError("invalid_query_plan", str(exc)) from exc

    _validate_start_date_clauses(merged)

    return merged, notes


def _is_proximity_geo(filter_geo: str | None) -> bool:
    if filter_geo is None:
        return False
    return bool(_GEO_DISTANCE_PATTERN.match(filter_geo.strip()))


def _inject_intent_filters(
    intent: Intent,
    draft_params: SearchParamsDraft,
    *,
    notes: list[str],
) -> SearchParamsDraft:
    updates: dict[str, Any] = {}
    filters = intent.filters

    if filters.drug_name and not draft_params.query_intr:
        updates["query_intr"] = filters.drug_name
        notes.append("Injected query_intr from intent drug_name.")
    if filters.condition and not draft_params.query_cond:
        updates["query_cond"] = filters.condition
        notes.append("Injected query_cond from intent condition.")
    if filters.sponsor and not draft_params.query_spons:
        updates["query_spons"] = filters.sponsor
        notes.append("Injected query_spons from intent sponsor.")
    if filters.country and not draft_params.query_locn:
        updates["query_locn"] = filters.country
        notes.append("Injected query_locn from intent country.")

    if not updates:
        return draft_params
    return draft_params.model_copy(update=updates)


def _apply_geographic_rules(
    intent: Intent,
    draft_params: SearchParamsDraft,
    *,
    notes: list[str],
) -> SearchParamsDraft:
    if intent.horizon is not Horizon.GEOGRAPHIC:
        return draft_params

    updates: dict[str, Any] = {}
    if intent.filters.country and not draft_params.query_locn:
        updates["query_locn"] = intent.filters.country
        notes.append("Set query_locn from intent country for geographic horizon.")

    filter_geo = draft_params.filter_geo
    if filter_geo and not _is_proximity_geo(filter_geo):
        updates["filter_geo"] = None
        if not updates.get("query_locn") and not draft_params.query_locn:
            updates["query_locn"] = filter_geo
        notes.append(
            "Cleared non-proximity filter_geo; using query_locn for named place."
        )

    if not updates:
        return draft_params
    return draft_params.model_copy(update=updates)


def _validate_overall_status(
    statuses: list[str] | None,
    enums: CtgovEnums,
) -> list[str] | None:
    if not statuses:
        return None
    validated: list[str] = []
    for status in statuses:
        try:
            validated.append(enums.validate_overall_status(status))
        except ValueError as exc:
            raise AgentError("invalid_query_plan", str(exc)) from exc
    return validated


def draft_to_search_params(
    intent: Intent,
    draft_params: SearchParamsDraft,
    *,
    enums: CtgovEnums,
    fields: list[str],
    page_size: int,
    notes: list[str],
) -> StudiesSearchParams:
    params = _inject_intent_filters(intent, draft_params, notes=notes)
    params = _apply_geographic_rules(intent, params, notes=notes)

    filter_advanced, advanced_notes = build_advanced_filters(
        intent,
        enums,
        params.filter_advanced,
    )
    notes.extend(advanced_notes)

    validated_status = _validate_overall_status(params.filter_overall_status, enums)

    raw: dict[str, Any] = params.model_dump()
    raw["filter_advanced"] = filter_advanced
    raw["filter_overall_status"] = validated_status
    raw["fields"] = fields
    raw["count_total"] = True
    raw["page_size"] = page_size
    raw.pop("page_token", None)

    try:
        return StudiesSearchParams.model_validate(raw)
    except ValidationError as exc:
        raise AgentError(
            "invalid_query_plan",
            f"Invalid search parameters: {exc}",
        ) from exc


def _normalize_search_draft(
    intent: Intent,
    search_draft: PlannedSearchDraft,
    *,
    enums: CtgovEnums,
    fields: list[str],
    page_size: int,
    label: str | None,
    notes: list[str],
) -> PlannedSearch:
    params = draft_to_search_params(
        intent,
        search_draft.params,
        enums=enums,
        fields=fields,
        page_size=page_size,
        notes=notes,
    )
    if fields != list(params.fields or []):
        notes.append("Set fields from horizon spec.")
    if params.count_total:
        notes.append("Set count_total=true and fields from horizon spec.")
    return PlannedSearch(label=label, params=params, fields=fields)


def normalize_query_plan(
    intent: Intent,
    draft: QueryPlanDraft,
    *,
    enums: CtgovEnums,
    page_size: int = 100,
) -> APIQueryPlan:
    if not draft.searches:
        raise AgentError(
            "invalid_query_plan",
            "Query plan must include at least one search.",
        )

    if intent.horizon is Horizon.COMPARISON:
        expected = len(intent.comparison_arm_labels)
        if len(draft.searches) != expected:
            raise AgentError(
                "invalid_query_plan",
                (
                    f"Comparison horizon requires {expected} searches, "
                    f"got {len(draft.searches)}."
                ),
            )

    fields = resolve_fields(intent)
    notes: list[str] = []
    searches: list[PlannedSearch] = []

    match intent.horizon:
        case Horizon.COMPARISON:
            for index, search_draft in enumerate(draft.searches):
                label = intent.comparison_arm_labels[index]
                searches.append(
                    _normalize_search_draft(
                        intent,
                        search_draft,
                        enums=enums,
                        fields=fields,
                        page_size=page_size,
                        label=label,
                        notes=notes,
                    )
                )
        case (
            Horizon.TIME_TREND
            | Horizon.DISTRIBUTION
            | Horizon.GEOGRAPHIC
            | Horizon.NETWORK
        ):
            for search_draft in draft.searches:
                searches.append(
                    _normalize_search_draft(
                        intent,
                        search_draft,
                        enums=enums,
                        fields=fields,
                        page_size=page_size,
                        label=search_draft.label,
                        notes=notes,
                    )
                )
        case _ as unreachable:
            assert_never(unreachable)

    deduped_notes = list(dict.fromkeys(notes))
    return APIQueryPlan(
        horizon=intent.horizon,
        searches=searches,
        normalization_notes=deduped_notes,
    )
