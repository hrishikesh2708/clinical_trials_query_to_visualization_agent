"""Tests for filter.advanced StartDate clause validation."""

import pytest

from app.agent.advanced_filter_validator import (
    find_invalid_start_date_clauses,
    is_valid_start_date_clause,
)


@pytest.mark.parametrize(
    "clause",
    [
        "AREA[StartDate]2015",
        "AREA[StartDate]2015-01-01",
        "AREA[StartDate]RANGE[2015-01-01,2018-12-31]",
        "AREA[StartDate]RANGE[2015-01-01,MAX]",
        "AREA[StartDate]RANGE[MIN,2018-12-31]",
    ],
)
def test_is_valid_start_date_clause_accepts_api_safe_formats(clause: str) -> None:
    assert is_valid_start_date_clause(clause)


@pytest.mark.parametrize(
    "clause",
    [
        "AREA[StartDate]2015-2018",
        "AREA[StartDate]RANGE[2015 to 2018]",
        "AREA[StartDate]RANGE[2015/01/01,2018/12/31]",
        "AREA[StartDate]RANGE[2015,2018]",
        "AREA[StartDate]since 2015",
    ],
)
def test_is_valid_start_date_clause_rejects_malformed_formats(clause: str) -> None:
    assert not is_valid_start_date_clause(clause)


def test_find_invalid_start_date_clauses_in_combined_expression() -> None:
    expression = (
        "AREA[Phase]PHASE3 AND AREA[StartDate]RANGE[2015-2018] "
        "AND AREA[StartDate]RANGE[2015-01-01,2018-12-31]"
    )
    invalid = find_invalid_start_date_clauses(expression)
    assert invalid == ["AREA[StartDate]RANGE[2015-2018]"]
