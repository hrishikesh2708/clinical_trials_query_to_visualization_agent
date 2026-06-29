"""FastAPI dependency injection for the visualize API."""

from fastapi import Depends, Request

from app.agent.pipeline import VisualizePipeline
from app.core.config import Settings
from app.infrastructure.ctgov.client import CtgovClient, ctgov_client_from_settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_ctgov_client(settings: Settings = Depends(get_settings)) -> CtgovClient:
    return ctgov_client_from_settings(settings)


def get_visualize_pipeline(
    settings: Settings = Depends(get_settings),
    ctgov: CtgovClient = Depends(get_ctgov_client),
) -> VisualizePipeline:
    return VisualizePipeline(settings, ctgov=ctgov)
