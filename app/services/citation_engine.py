"""Build citations from study JSON with per-datum caps."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Hashable
from typing import Any, TypeVar

from app.core.schemas.visualization import Citation
from app.domain import models as study_models

MAX_CITATIONS_PER_DATUM = 5

ExcerptBuilder = Callable[[dict[str, Any]], str]
K = TypeVar("K", bound=Hashable)


def _require_nct_id(study: dict[str, Any]) -> str:
    nct_id = study_models.nct_id(study)
    if nct_id is None:
        raise ValueError("Study is missing nctId")
    return nct_id


def _json_string_literal(value: str) -> str:
    """How ``value`` appears inside ``json.dumps`` output (without outer quotes)."""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def _excerpt_from_study_json(study: dict[str, Any], excerpt: str) -> str:
    serialized = json.dumps(study, ensure_ascii=False)
    if excerpt in serialized:
        return excerpt
    escaped = _json_string_literal(excerpt)
    if escaped in serialized:
        return escaped
    raise ValueError(f"Excerpt not found in study JSON: {excerpt!r}")


def make_citation(
    study: dict[str, Any],
    *,
    excerpt_builder: ExcerptBuilder,
) -> Citation:
    excerpt = excerpt_builder(study)
    return Citation(nct_id=_require_nct_id(study), excerpt=excerpt)


def excerpt_start_date(study: dict[str, Any]) -> str:
    struct = study_models.start_date_struct(study)
    if struct is None:
        raise ValueError("Study is missing startDateStruct")
    date_value = struct.get("date")
    if not isinstance(date_value, str) or not date_value:
        raise ValueError("Study is missing startDateStruct.date")
    return _excerpt_from_study_json(study, date_value)


def excerpt_phase(study: dict[str, Any], phase_code: str) -> str:
    return _excerpt_from_study_json(study, phase_code)


def excerpt_overall_status(study: dict[str, Any]) -> str:
    status = study_models.overall_status(study)
    if status is None:
        raise ValueError("Study is missing overallStatus")
    return _excerpt_from_study_json(study, status)


def excerpt_enrollment(study: dict[str, Any]) -> str:
    count = study_models.enrollment_count(study)
    if count is None:
        raise ValueError("Study is missing enrollment count")
    return _excerpt_from_study_json(study, str(count))


def excerpt_country(study: dict[str, Any], country: str) -> str:
    return _excerpt_from_study_json(study, country)


def excerpt_intervention(study: dict[str, Any], name: str) -> str:
    return _excerpt_from_study_json(study, name)


def excerpt_sponsor(study: dict[str, Any]) -> str:
    sponsor = study_models.lead_sponsor_name(study)
    if sponsor is None:
        raise ValueError("Study is missing lead sponsor name")
    return _excerpt_from_study_json(study, sponsor)


def excerpt_phase_for_study(study: dict[str, Any]) -> str:
    phases = study_models.phases(study)
    if phases:
        return excerpt_phase(study, phases[0])
    nct_id = study_models.nct_id(study)
    if nct_id is None:
        raise ValueError("Study is missing nctId")
    return _excerpt_from_study_json(study, nct_id)


def excerpt_condition(study: dict[str, Any], condition: str) -> str:
    return _excerpt_from_study_json(study, condition)


def build_citations_for_studies(
    studies: list[dict[str, Any]],
    *,
    excerpt_builder: ExcerptBuilder,
) -> list[Citation]:
    citations: list[Citation] = []
    for study in studies:
        try:
            citations.append(
                make_citation(study, excerpt_builder=excerpt_builder)
            )
        except ValueError:
            continue
    citations.sort(key=lambda item: item.nct_id)
    return citations[:MAX_CITATIONS_PER_DATUM]


def attach_citations(
    bucket_map: dict[K, list[dict[str, Any]]],
    *,
    excerpt_builder: ExcerptBuilder,
) -> dict[K, list[Citation]]:
    return {
        key: build_citations_for_studies(studies, excerpt_builder=excerpt_builder)
        for key, studies in bucket_map.items()
    }


BucketExcerptBuilder = Callable[[dict[str, Any], K], str]


def attach_citations_per_bucket(
    bucket_map: dict[K, list[dict[str, Any]]],
    *,
    excerpt_builder: BucketExcerptBuilder,
) -> dict[K, list[Citation]]:
    return {
        key: build_citations_for_studies(
            studies,
            excerpt_builder=lambda study, bucket_key=key: excerpt_builder(
                study, bucket_key
            ),
        )
        for key, studies in bucket_map.items()
    }


def slug_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "unknown"
