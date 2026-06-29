"""Tests for intent filter sanitization after LLM merge."""

from app.agent.intent_filter_sanitizer import sanitize_intent_filters
from app.agent.types import Intent, ResolvedFilters
from app.domain.horizons import Horizon


def _intent(**filter_updates: object) -> Intent:
    return Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(**filter_updates),
    )


def test_sanitize_keeps_valid_start_year() -> None:
    intent = _intent(start_year=2015)
    sanitized = sanitize_intent_filters(intent)
    assert sanitized.filters.start_year == 2015
    assert sanitized.assumptions == []


def test_sanitize_nulls_out_of_range_start_year() -> None:
    intent = _intent(start_year=1800)
    sanitized = sanitize_intent_filters(intent)
    assert sanitized.filters.start_year is None
    assert any("invalid start_year=1800" in note for note in sanitized.assumptions)


def test_sanitize_nulls_conflicting_year_range() -> None:
    intent = _intent(start_year=2022, end_year=2018)
    sanitized = sanitize_intent_filters(intent)
    assert sanitized.filters.start_year is None
    assert sanitized.filters.end_year is None
    assert any("conflicting date range" in note for note in sanitized.assumptions)


def test_sanitize_no_op_for_open_filters() -> None:
    intent = _intent()
    sanitized = sanitize_intent_filters(intent)
    assert sanitized.filters.start_year is None
    assert sanitized.filters.end_year is None
    assert sanitized.assumptions == []
