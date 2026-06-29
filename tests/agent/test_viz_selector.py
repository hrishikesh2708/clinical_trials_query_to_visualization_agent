"""Tests for Step 4 visualization type selector."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.exceptions import AgentError
from app.agent.types import (
    FetchPreview,
    Intent,
    ResolvedFilters,
    SearchPreview,
    VizSelection,
)
from app.agent.viz_selector import apply_viz_gate, select_viz
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType


def _intent(**updates: object) -> Intent:
    base = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(),
    )
    return base.model_copy(update=updates)


def _preview(
    allowed: list[VisualizationType],
    *,
    studies_fetched: int = 10,
) -> FetchPreview:
    return FetchPreview(
        searches=[
            SearchPreview(
                label=None,
                studies_fetched=studies_fetched,
                total_count=20,
            )
        ],
        allowed_viz_types=allowed,
    )


def test_apply_viz_gate_accepts_valid_selection() -> None:
    preview = _preview([VisualizationType.TIME_SERIES])
    result = apply_viz_gate(
        _intent(),
        VizSelection(viz_type=VisualizationType.TIME_SERIES),
        preview,
    )
    assert result is VisualizationType.TIME_SERIES


def test_apply_viz_gate_sole_allowed_fallback() -> None:
    preview = _preview([VisualizationType.TIME_SERIES])
    result = apply_viz_gate(
        _intent(),
        VizSelection(viz_type=VisualizationType.BAR_CHART),
        preview,
    )
    assert result is VisualizationType.TIME_SERIES


def test_apply_viz_gate_suggested_viz_type_fallback() -> None:
    preview = _preview(
        [VisualizationType.BAR_CHART, VisualizationType.HISTOGRAM],
    )
    intent = _intent(
        horizon=Horizon.DISTRIBUTION,
        bucket_field="phase",
        suggested_viz_type=VisualizationType.HISTOGRAM,
    )
    result = apply_viz_gate(
        intent,
        VizSelection(viz_type=VisualizationType.TIME_SERIES),
        preview,
    )
    assert result is VisualizationType.HISTOGRAM


def test_apply_viz_gate_heuristic_enrollment_histogram() -> None:
    preview = _preview(
        [VisualizationType.BAR_CHART, VisualizationType.HISTOGRAM],
    )
    intent = _intent(
        horizon=Horizon.DISTRIBUTION,
        bucket_field="enrollment",
    )
    result = apply_viz_gate(
        intent,
        VizSelection(viz_type=VisualizationType.TIME_SERIES),
        preview,
    )
    assert result is VisualizationType.HISTOGRAM


def test_apply_viz_gate_raises_incompatible_horizon_viz() -> None:
    preview = _preview(
        [VisualizationType.BAR_CHART, VisualizationType.HISTOGRAM],
    )
    intent = _intent(horizon=Horizon.NETWORK)
    with pytest.raises(AgentError) as exc_info:
        apply_viz_gate(
            intent,
            VizSelection(viz_type=VisualizationType.TIME_SERIES),
            preview,
        )
    assert exc_info.value.code == "incompatible_horizon_viz"


def test_select_viz_retries_on_invalid_first_pick() -> None:
    preview = _preview([VisualizationType.TIME_SERIES])
    client = AsyncMock()

    with patch(
        "app.agent.viz_selector.parse_structured",
        new_callable=AsyncMock,
        side_effect=[
            VizSelection(viz_type=VisualizationType.BAR_CHART),
            VizSelection(viz_type=VisualizationType.TIME_SERIES),
        ],
    ) as mock_parse:
        result = asyncio.run(
            select_viz(
                _intent(),
                preview,
                client=client,
                model="gpt-4o-mini",
            )
        )

    assert result is VisualizationType.TIME_SERIES
    assert mock_parse.await_count == 2


def test_select_viz_uses_fallback_after_retry_still_invalid() -> None:
    preview = _preview([VisualizationType.TIME_SERIES])
    client = AsyncMock()

    with patch(
        "app.agent.viz_selector.parse_structured",
        new_callable=AsyncMock,
        return_value=VizSelection(viz_type=VisualizationType.BAR_CHART),
    ) as mock_parse:
        result = asyncio.run(
            select_viz(
                _intent(),
                preview,
                client=client,
                model="gpt-4o-mini",
            )
        )

    assert result is VisualizationType.TIME_SERIES
    assert mock_parse.await_count == 2
