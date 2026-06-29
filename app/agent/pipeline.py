"""Linear orchestrator for the visualize pipeline."""

from __future__ import annotations

from openai import AsyncOpenAI

from app.agent.types import (
    APIQueryPlan,
    FetchResult,
    Intent,
)
from app.core.config import Settings
from app.core.schemas.request import VisualizeRequest
from app.core.schemas.response import VisualizeResponse
from app.core.schemas.visualization import Visualization
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.client import CtgovClient, ctgov_client_from_settings


class VisualizePipeline:
    def __init__(
        self,
        settings: Settings,
        *,
        ctgov: CtgovClient | None = None,
        openai_client: AsyncOpenAI | None = None,
    ) -> None:
        self._settings = settings
        self._ctgov = ctgov or ctgov_client_from_settings(settings)
        self._openai = openai_client or AsyncOpenAI(api_key=settings.openai_api_key)

    async def run(self, request: VisualizeRequest) -> VisualizeResponse:
        intent = await self._step1_parse_intent(request)
        plan = await self._step2_plan_query(intent)
        fetched = await self._step3_fetch_studies(plan)
        viz_type = await self._step4_select_viz(intent, fetched)
        viz = await self._step5_transform(intent, plan, fetched, viz_type)
        return await self._step6_build_response(
            request, intent, plan, fetched, viz_type, viz
        )

    async def _step1_parse_intent(self, request: VisualizeRequest) -> Intent:
        raise NotImplementedError("Stage 8b")

    async def _step2_plan_query(self, intent: Intent) -> APIQueryPlan:
        raise NotImplementedError("Stage 8c")

    async def _step3_fetch_studies(self, plan: APIQueryPlan) -> FetchResult:
        raise NotImplementedError("Stage 8d")

    async def _step4_select_viz(
        self, intent: Intent, fetched: FetchResult
    ) -> VisualizationType:
        raise NotImplementedError("Stage 8d")

    async def _step5_transform(
        self,
        intent: Intent,
        plan: APIQueryPlan,
        fetched: FetchResult,
        viz_type: VisualizationType,
    ) -> Visualization:
        raise NotImplementedError("Stage 8e")

    async def _step6_build_response(
        self,
        request: VisualizeRequest,
        intent: Intent,
        plan: APIQueryPlan,
        fetched: FetchResult,
        viz_type: VisualizationType,
        viz: Visualization,
    ) -> VisualizeResponse:
        raise NotImplementedError("Stage 8e")
