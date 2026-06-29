"""Validate and sanitize LLM-merged intent filters before query planning."""

from __future__ import annotations

from app.agent.types import Intent, ResolvedFilters

_MIN_YEAR = 1900
_MAX_YEAR = 2100


def _valid_year(year: int) -> bool:
    return _MIN_YEAR <= year <= _MAX_YEAR


def sanitize_resolved_filters(
    filters: ResolvedFilters,
) -> tuple[ResolvedFilters, list[str]]:
    """Null invalid years and record assumptions; does not extract from query text."""
    notes: list[str] = []
    updates: dict[str, None] = {}

    start_year = filters.start_year
    end_year = filters.end_year

    if start_year is not None and not _valid_year(start_year):
        updates["start_year"] = None
        notes.append(
            f"Removed invalid start_year={start_year}; must be between "
            f"{_MIN_YEAR} and {_MAX_YEAR}."
        )
        start_year = None

    if end_year is not None and not _valid_year(end_year):
        updates["end_year"] = None
        notes.append(
            f"Removed invalid end_year={end_year}; must be between "
            f"{_MIN_YEAR} and {_MAX_YEAR}."
        )
        end_year = None

    if (
        start_year is not None
        and end_year is not None
        and start_year > end_year
    ):
        updates["start_year"] = None
        updates["end_year"] = None
        notes.append(
            f"Removed conflicting date range start_year={start_year}, "
            f"end_year={end_year}; start_year must be <= end_year."
        )

    if not updates:
        return filters, notes

    return filters.model_copy(update=updates), notes


def sanitize_intent_filters(intent: Intent) -> Intent:
    updated_filters, notes = sanitize_resolved_filters(intent.filters)
    if not notes:
        return intent

    return intent.model_copy(
        update={
            "filters": updated_filters,
            "assumptions": [*intent.assumptions, *notes],
        }
    )
