"""HTTP client for the visualize FastAPI backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True, slots=True)
class BackendError(Exception):
    status_code: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def default_backend_url() -> str:
    return os.environ.get("BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")


def check_health(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url}/health", timeout=5.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def fetch_visualization(
    request_body: dict[str, Any],
    base_url: str,
) -> dict[str, Any]:
    """POST to /api/v1/visualize and return parsed JSON."""
    url = f"{base_url.rstrip('/')}/api/v1/visualize"
    try:
        response = httpx.post(
            url,
            json=request_body,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException as exc:
        raise BackendError(
            status_code=0,
            code="timeout",
            message=(
                "Request timed out. The pipeline may still be running on the "
                "backend — check server logs or try again."
            ),
        ) from exc
    except httpx.HTTPError as exc:
        raise BackendError(
            status_code=0,
            code="connection_error",
            message=f"Could not reach backend at {base_url}: {exc}",
        ) from exc

    if response.status_code == 200:
        return response.json()

    detail = _parse_error_detail(response)
    raise BackendError(
        status_code=response.status_code,
        code=detail["code"],
        message=detail["message"],
    )


def _parse_error_detail(response: httpx.Response) -> dict[str, str]:
    try:
        payload = response.json()
    except ValueError:
        return {
            "code": "http_error",
            "message": f"HTTP {response.status_code}: {response.text[:200]}",
        }

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return {
            "code": str(detail.get("code", "error")),
            "message": str(detail.get("message", "Unknown error")),
        }
    if isinstance(detail, str):
        return {"code": "error", "message": detail}

    return {
        "code": "http_error",
        "message": f"HTTP {response.status_code}",
    }
