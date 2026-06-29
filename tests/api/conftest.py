"""Shared fixtures for API integration tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_visualize_pipeline
from app.main import app
from tests.api.horizon_mocks import build_mock_pipeline


@pytest.fixture
def client() -> Iterator[TestClient]:
    pipeline = build_mock_pipeline()
    app.dependency_overrides[get_visualize_pipeline] = lambda: pipeline
    yield TestClient(app)
    app.dependency_overrides.clear()
