"""Canonical sample queries — two per horizon (matches manifest.json)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SampleQuery:
    label: str
    request: dict[str, str | int | None]


SAMPLE_QUERIES: tuple[SampleQuery, ...] = (
    SampleQuery(
        label="Pembrolizumab trials per year since 2015",
        request={
            "query": (
                "How has the number of trials for Pembrolizumab "
                "changed per year since 2015"
            ),
        },
    ),
    SampleQuery(
        label="Diabetes trials started each year",
        request={
            "query": "How many trials started each year for diabetes",
        },
    ),
    SampleQuery(
        label="Breast cancer trials by phase",
        request={
            "query": "How are breast cancer trials distributed across phases?",
        },
    ),
    SampleQuery(
        label="Diabetes trials by recruitment status",
        request={
            "query": (
                "What is the recruitment status breakdown for diabetes trials?"
            ),
        },
    ),
    SampleQuery(
        label="Pembrolizumab vs nivolumab by phase",
        request={
            "query": (
                "Compare phases for trials involving pembrolizumab vs nivolumab"
            ),
        },
    ),
    SampleQuery(
        label="Breast cancer vs lung cancer by phase",
        request={
            "query": (
                "Compare breast cancer vs lung cancer trial counts by phase"
            ),
        },
    ),
    SampleQuery(
        label="Recruiting lung cancer trials by country",
        request={
            "query": "Recruiting lung cancer trials by country",
        },
    ),
    SampleQuery(
        label="Countries running pembrolizumab trials",
        request={
            "query": "Countries running pembrolizumab trials",
        },
    ),
    SampleQuery(
        label="Diabetes sponsor and drug network",
        request={
            "query": (
                "Show a network of sponsors and drugs for diabetes trials"
            ),
        },
    ),
    SampleQuery(
        label="Melanoma drug co-occurrence network",
        request={
            "query": (
                "Which drugs frequently co-occur in combination melanoma trials?"
            ),
        },
    ),
)

FILTER_FIELDS: tuple[str, ...] = (
    "drug_name",
    "condition",
    "trial_phase",
    "sponsor",
    "country",
    "start_year",
    "end_year",
)


def sample_select_options() -> list[str]:
    """Return display labels for the sample query selectbox."""
    return [sample.label for sample in SAMPLE_QUERIES]


def sample_by_label(label: str) -> SampleQuery | None:
    for sample in SAMPLE_QUERIES:
        if sample.label == label:
            return sample
    return None
