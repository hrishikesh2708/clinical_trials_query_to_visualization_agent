"""HTTP exception handlers for the visualize API."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.agent.exceptions import AgentError
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.validation.viz_compatibility import VizValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AgentError)
    async def agent_error_handler(
        _request: Request, exc: AgentError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(VizValidationError)
    async def viz_validation_error_handler(
        _request: Request, exc: VizValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(CtgovRateLimitError)
    async def ctgov_rate_limit_error_handler(
        _request: Request, exc: CtgovRateLimitError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "detail": {"code": "ctgov_rate_limited", "message": str(exc)},
            },
        )

    @app.exception_handler(CtgovApiError)
    async def ctgov_api_error_handler(
        _request: Request, exc: CtgovApiError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "detail": {
                    "code": "ctgov_api_error",
                    "message": str(exc),
                    "upstream_status": exc.status_code,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, _exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                },
            },
        )
