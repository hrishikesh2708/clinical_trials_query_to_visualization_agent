"""Tests for VisualizePipeline scaffolding."""

import asyncio

import pytest

from app.agent.pipeline import VisualizePipeline
from app.core.config import Settings
from app.core.schemas.request import VisualizeRequest


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def pipeline(settings: Settings) -> VisualizePipeline:
    return VisualizePipeline(settings)


def test_pipeline_run_raises_at_step1(pipeline: VisualizePipeline) -> None:
    request = VisualizeRequest(query="Trials for pembrolizumab since 2015")
    with pytest.raises(NotImplementedError, match="Stage 8b"):
        asyncio.run(pipeline.run(request))


def test_pipeline_constructs_with_defaults(settings: Settings) -> None:
    pipeline = VisualizePipeline(settings)
    assert pipeline._ctgov is not None
    assert pipeline._openai is not None
