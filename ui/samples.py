"""Canonical sample queries — one per horizon."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SampleQuery:
    horizon: str
    label: str
    verification: bool
    request: dict[str, str | int | None]


SAMPLE_QUERIES: tuple[SampleQuery, ...] = (
    SampleQuery(
        horizon="geographic",
        label="Recruiting lung cancer trials by country",
        verification=True,
        request={"query": "Recruiting lung cancer trials by country"},
    ),
    SampleQuery(
        horizon="network",
        label="Diabetes sponsor and drug network",
        verification=True,
        request={"query": "Diabetes sponsor and drug network"},
    ),
    SampleQuery(
        horizon="time_trend",
        label="Pembrolizumab trials per year since 2015",
        verification=False,
        request={
            "query": (
                "How has the number of trials for Pembrolizumab "
                "changed per year since 2015"
            ),
        },
    ),
    SampleQuery(
        horizon="distribution",
        label="Breast cancer trials by phase",
        verification=False,
        request={
            "query": "How are breast cancer trials distributed across phases?",
        },
    ),
    SampleQuery(
        horizon="comparison",
        label="Pembrolizumab vs nivolumab by phase",
        verification=False,
        request={
            "query": (
                "Compare phases for trials involving pembrolizumab vs nivolumab"
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
