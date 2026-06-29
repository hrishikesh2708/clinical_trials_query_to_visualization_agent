"""Tests for query planner LLM integration (mocked)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.exceptions import AgentError
from app.agent.query_planner import plan_query
from app.agent.types import (
    Intent,
    PlannedSearchDraft,
    QueryPlanDraft,
    ResolvedFilters,
    SearchParamsDraft,
)
from app.domain.horizons import Horizon
from app.infrastructure.ctgov.enums import CtgovEnumsLoader
from tests.agent.conftest import enums_from_fixture


def _enums_loader() -> CtgovEnumsLoader:
    loader = MagicMock(spec=CtgovEnumsLoader)
    loader.load.return_value = enums_from_fixture()
    return loader


def test_plan_query_distribution_matches_spec_example() -> None:
    intent = Intent(
        horizon=Horizon.DISTRIBUTION,
        filters=ResolvedFilters(),
        bucket_field="phase",
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(query_cond="breast cancer"),
            )
        ]
    )
    client = AsyncMock()

    with patch(
        "app.agent.query_planner.parse_structured",
        new_callable=AsyncMock,
        return_value=draft,
    ):
        plan = asyncio.run(
            plan_query(
                intent,
                client=client,
                model="gpt-4o-mini",
                enums_loader=_enums_loader(),
            )
        )

    assert plan.horizon is Horizon.DISTRIBUTION
    assert plan.searches[0].params.query_cond == "breast cancer"
    assert plan.searches[0].fields == ["NCTId", "Phase"]
    assert plan.searches[0].params.count_total is True


def test_plan_query_comparison_matches_spec_example() -> None:
    intent = Intent(
        horizon=Horizon.COMPARISON,
        filters=ResolvedFilters(),
        comparison_arm_labels=("Pembrolizumab", "Nivolumab"),
        bucket_field="phase",
    )
    draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(query_intr="Pembrolizumab"),
            ),
            PlannedSearchDraft(
                params=SearchParamsDraft(query_intr="Nivolumab"),
            ),
        ]
    )
    client = AsyncMock()

    with patch(
        "app.agent.query_planner.parse_structured",
        new_callable=AsyncMock,
        return_value=draft,
    ):
        plan = asyncio.run(
            plan_query(
                intent,
                client=client,
                model="gpt-4o-mini",
                enums_loader=_enums_loader(),
            )
        )

    assert len(plan.searches) == 2
    assert plan.searches[0].label == "Pembrolizumab"
    assert plan.searches[1].label == "Nivolumab"
    assert plan.searches[0].params.query_intr == "Pembrolizumab"
    assert plan.searches[1].params.query_intr == "Nivolumab"


def test_plan_query_retries_once_on_invalid_query_plan() -> None:
    intent = Intent(
        horizon=Horizon.DISTRIBUTION,
        filters=ResolvedFilters(),
        bucket_field="phase",
    )
    bad_draft = QueryPlanDraft(searches=[])
    good_draft = QueryPlanDraft(
        searches=[
            PlannedSearchDraft(
                params=SearchParamsDraft(query_cond="breast cancer"),
            )
        ]
    )
    client = AsyncMock()

    with patch(
        "app.agent.query_planner.parse_structured",
        new_callable=AsyncMock,
        side_effect=[bad_draft, good_draft],
    ) as mock_parse:
        plan = asyncio.run(
            plan_query(
                intent,
                client=client,
                model="gpt-4o-mini",
                enums_loader=_enums_loader(),
            )
        )

    assert mock_parse.await_count == 2
    assert plan.searches[0].params.query_cond == "breast cancer"


def test_plan_query_raises_after_second_invalid_query_plan() -> None:
    intent = Intent(
        horizon=Horizon.DISTRIBUTION,
        filters=ResolvedFilters(),
        bucket_field="phase",
    )
    bad_draft = QueryPlanDraft(searches=[])
    client = AsyncMock()

    with patch(
        "app.agent.query_planner.parse_structured",
        new_callable=AsyncMock,
        return_value=bad_draft,
    ) as mock_parse:
        with pytest.raises(AgentError) as exc_info:
            asyncio.run(
                plan_query(
                    intent,
                    client=client,
                    model="gpt-4o-mini",
                    enums_loader=_enums_loader(),
                )
            )

    assert exc_info.value.code == "invalid_query_plan"
    assert mock_parse.await_count == 2
