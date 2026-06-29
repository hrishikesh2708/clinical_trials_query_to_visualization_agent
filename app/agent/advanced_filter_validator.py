"""Validate ClinicalTrials.gov filter.advanced Essie clauses before API calls."""

from __future__ import annotations

import re

_AND_SPLIT_PATTERN = re.compile(r"\s+AND\s+", re.IGNORECASE)

_START_DATE_CLAUSE_DETECT = re.compile(r"^AREA\[StartDate\]", re.IGNORECASE)

_VALID_START_DATE_CLAUSE = re.compile(
    r"^AREA\[StartDate\](?:"
    r"\d{4}|"
    r"\d{4}-\d{2}-\d{2}|"
    r"RANGE\[(?:MIN|\d{4}-\d{2}-\d{2}),(?:MAX|\d{4}-\d{2}-\d{2})\]"
    r")$",
    re.IGNORECASE,
)


def split_and_clauses(expression: str) -> list[str]:
    return [
        clause.strip()
        for clause in _AND_SPLIT_PATTERN.split(expression.strip())
        if clause.strip()
    ]


def is_start_date_clause(clause: str) -> bool:
    return bool(_START_DATE_CLAUSE_DETECT.match(clause.strip()))


def is_valid_start_date_clause(clause: str) -> bool:
    return bool(_VALID_START_DATE_CLAUSE.match(clause.strip()))


def find_invalid_start_date_clauses(expression: str | None) -> list[str]:
    if not expression or not expression.strip():
        return []
    return [
        clause
        for clause in split_and_clauses(expression)
        if is_start_date_clause(clause) and not is_valid_start_date_clause(clause)
    ]
