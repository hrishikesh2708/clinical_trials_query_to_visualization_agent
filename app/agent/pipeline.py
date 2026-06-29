"""Linear orchestrator for the visualize pipeline."""

from __future__ import annotations

from openai import AsyncOpenAI

from app.agent.api_caller import fetch_studies
from app.agent.intent_parser import parse_intent
from app.agent.query_planner import plan_query
from app.agent.response_builder import build_visualize_response
from app.agent.transform_wiring import run_transform
from app.agent.types import (
    APIQueryPlan,
    FetchResult,
    Intent,
)
from app.agent.viz_selector import select_viz
from app.core.config import Settings
from app.core.schemas.request import VisualizeRequest
from app.core.schemas.response import VisualizeResponse
from app.core.schemas.visualization import Visualization
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.client import CtgovClient, ctgov_client_from_settings
from app.infrastructure.ctgov.enums import CtgovEnumsLoader


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
        self._enums_loader = CtgovEnumsLoader(self._ctgov)

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
        return await parse_intent(
            request,
            client=self._openai,
            model=self._settings.openai_model,
        )

    async def _step2_plan_query(self, intent: Intent) -> APIQueryPlan:
        return await plan_query(
            intent,
            client=self._openai,
            model=self._settings.openai_model,
            enums_loader=self._enums_loader,
        )

    async def _step3_fetch_studies(self, plan: APIQueryPlan) -> FetchResult:
        return fetch_studies(plan, self._ctgov)

    async def _step4_select_viz(
        self, intent: Intent, fetched: FetchResult
    ) -> VisualizationType:
        return await select_viz(
            intent,
            fetched.preview,
            client=self._openai,
            model=self._settings.openai_model,
        )

    async def _step5_transform(
        self,
        intent: Intent,
        plan: APIQueryPlan,
        fetched: FetchResult,
        viz_type: VisualizationType,
    ) -> Visualization:
        return run_transform(
            intent,
            plan,
            fetched,
            viz_type,
            self._enums_loader.load(),
        )

    async def _step6_build_response(
        self,
        request: VisualizeRequest,
        intent: Intent,
        plan: APIQueryPlan,
        fetched: FetchResult,
        viz_type: VisualizationType,
        viz: Visualization,
    ) -> VisualizeResponse:
        _ = request
        _ = plan
        return await build_visualize_response(
            intent,
            viz,
            viz_type,
            fetched,
            client=self._openai,
            model=self._settings.openai_model,
        )
