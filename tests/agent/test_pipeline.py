"""Tests for VisualizePipeline scaffolding."""

import pytest

from app.agent.pipeline import VisualizePipeline
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def pipeline(settings: Settings) -> VisualizePipeline:
    return VisualizePipeline(settings)


def test_pipeline_constructs_with_defaults(settings: Settings) -> None:
    pipeline = VisualizePipeline(settings)
    assert pipeline._ctgov is not None
    assert pipeline._openai is not None
    assert pipeline._enums_loader is not None
