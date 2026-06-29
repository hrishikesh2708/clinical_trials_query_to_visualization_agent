"""Canonical sample queries — one per horizon."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SampleQuery:
    label: str
    request: dict[str, str | int | None]


SAMPLE_QUERIES: tuple[SampleQuery, ...] = (
    SampleQuery(
        label="What is the phase distribution of lung cancer clinical trials",
        request={
            "query": (
                "What is the phase distribution of lung cancer clinical trials"
            ),
        },
    ),
    SampleQuery(
        label="What is the recruitment status breakdown for diabetes trials",
        request={
            "query": (
                "What is the recruitment status breakdown for diabetes trials"
            ),
        },
    ),
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
        label="Breast cancer trials by phase",
        request={
            "query": "How are breast cancer trials distributed across phases?",
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
        label="How many pembrolizumab trials are recruiting vs completed?",
        request={
            "query": (
                "How many pembrolizumab trials are recruiting vs completed?"
            ),
        },
    ),
    SampleQuery(
        label="Show breast cancer trials by overall status",
        request={
            "query": (
                "Show breast cancer trials by overall status"
            ),
        },
    ),
    SampleQuery(
        label="What intervention types are most common in Alzheimer's trials?",
        request={
            "query": (
                "What intervention types are most common in Alzheimer's trials?"
            ),
        },
    ),
    SampleQuery(
        label="Distribution of intervention types for melanoma trials",
        request={
            "query": (
                "Distribution of intervention types for melanoma trials"
            ),
        },
    ),
    SampleQuery(
        label="Histogram of trial sizes for phase 3 oncology studies",
        request={
            "query": (
                "Histogram of trial sizes for phase 3 oncology studies"
            ),
        },
    ),
    SampleQuery(
        label="How are nivolumab trials spread across phases?",
        request={
            "query": (
                "How are nivolumab trials spread across phases?"
            ),
        },
    ),
    SampleQuery(
        label="Pfizer-sponsored oncology trials by phase",
        request={
            "query": (
                "Pfizer-sponsored oncology trials by phase"
            ),
        },
    ),
    SampleQuery(
        label="Compare total trial counts for adalimumab vs etanercept",
        request={
            "query": (
                "Compare total trial counts for adalimumab vs etanercept"
            ),
        },
    ),
    SampleQuery(
        label="Compare breast cancer vs lung cancer trial counts by phase",
        request={
            "query": (
                "Compare breast cancer vs lung cancer trial counts by phase"
            ),
        },
    ),
    SampleQuery(
        label="How many diabetes trials are there compared to hypertension trials?",
        request={
            "query": (
                "How many diabetes trials are there compared to hypertension trials?"
            ),
        },
    ),
    SampleQuery(
        label="Compare overall status breakdown for Alzheimer's vs Parkinson's trials",
        request={
            "query": (
                "Compare overall status breakdown for Alzheimer's vs Parkinson's trials"
            ),
        },
    ),
    SampleQuery(
        label="Compare industry vs academic sponsor trials for diabetes",
        request={
            "query": (
                "Compare industry vs academic sponsor trials for diabetes"
            ),
        },
    ),
    SampleQuery(
        label="Industry vs academic sponsored breast cancer trials by phase",
        request={
            "query": (
                "Industry vs academic sponsored breast cancer trials by phase"
            ),
        },
    ),
    SampleQuery(
        label="Compare Pfizer vs Novartis oncology trials by phase",
        request={
            "query": (
                "Compare Pfizer vs Novartis oncology trials by phase"
            ),
        },
    ),
    SampleQuery(
        label="Pembrolizumab vs nivolumab recruiting trials since 2018",
        request={
            "query": (
                "Pembrolizumab vs nivolumab recruiting trials since 2018"
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
