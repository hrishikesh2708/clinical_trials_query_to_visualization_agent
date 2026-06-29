"""Shared urllib mocks for ClinicalTrials.gov client tests."""

from __future__ import annotations

import io
import json
import urllib.error
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse


def query_param(url: str, key: str) -> str:
    values = parse_qs(urlparse(url).query).get(key)
    if not values:
        raise KeyError(key)
    return values[0]


def url_path(url: str) -> str:
    return urlparse(url).path


@contextmanager
def mock_ctgov_urlopen(
    responses: list[dict[str, Any]],
) -> Iterator[Callable[[], list[str]]]:
    """Mock urllib.request.urlopen for CtgovClient tests.

    Each response spec may include:
      - json: dict or list (serialized as JSON; default status 200)
      - status_code: HTTP status (default 200)
      - text: raw response body when json is omitted
      - reason: HTTP reason phrase for error responses
    """
    urls: list[str] = []
    call_idx = 0

    def urlopen(
        request: urllib.request.Request,
        timeout: float | None = None,
    ) -> object:
        nonlocal call_idx
        urls.append(request.full_url)
        if call_idx >= len(responses):
            raise AssertionError(
                f"Unexpected urlopen call #{call_idx + 1}: {request.full_url}"
            )
        spec = responses[call_idx]
        call_idx += 1

        status = spec.get("status_code", 200)
        if "json" in spec:
            body = json.dumps(spec["json"]).encode()
        else:
            body = spec.get("text", "").encode()

        if status >= 400:
            raise urllib.error.HTTPError(
                request.full_url,
                status,
                spec.get("reason", "Error"),
                {},
                io.BytesIO(body),
            )

        mock_resp = _MockHTTPResponse(status=status, body=body)
        return mock_resp

    with patch(
        "app.infrastructure.ctgov.transport.urllib.request.urlopen",
        side_effect=urlopen,
    ):
        yield lambda: urls


class _MockHTTPResponse:
    def __init__(self, *, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _MockHTTPResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        return False
