"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.visualize import router as visualize_router

router = APIRouter(prefix="/api/v1")
router.include_router(visualize_router)
