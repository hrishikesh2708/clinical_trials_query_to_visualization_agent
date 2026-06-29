"""POST /visualize — query-to-visualization endpoint."""

from fastapi import APIRouter, Depends

from app.agent.pipeline import VisualizePipeline
from app.api.dependencies import get_visualize_pipeline
from app.core.schemas.request import VisualizeRequest
from app.core.schemas.response import VisualizeResponse

router = APIRouter(tags=["visualize"])


@router.post("/visualize", response_model=VisualizeResponse)
async def visualize(
    body: VisualizeRequest,
    pipeline: VisualizePipeline = Depends(get_visualize_pipeline),
) -> VisualizeResponse:
    return await pipeline.run(body)
