from collections.abc import Iterator
from typing import Any

import httpx

from app.core.config import Settings
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.models import (
    NCT_ID_PATTERN,
    StudiesSearchParams,
    StudiesSearchResult,
    StudyGetParams,
)


class CtgovClient:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        pagination_cap: int = 1000,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._pagination_cap = pagination_cap

    def _get(self, path: str, params: dict[str, str]) -> httpx.Response:
        url = f"{self._base_url}{path}"
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.get(url, params=params)
        if response.status_code == 429:
            raise CtgovRateLimitError(response.status_code, response.text)
        if response.status_code >= 400:
            raise CtgovApiError(response.status_code, response.text)
        return response

    def search_studies(self, params: StudiesSearchParams) -> StudiesSearchResult:
        response = self._get("/studies", params.to_query_params())
        data = response.json()
        return StudiesSearchResult(
            studies=data.get("studies", []),
            next_page_token=data.get("nextPageToken"),
            total_count=data.get("totalCount"),
        )

    def get_study(
        self,
        nct_id: str,
        params: StudyGetParams | None = None,
    ) -> dict[str, Any]:
        if not NCT_ID_PATTERN.match(nct_id):
            raise ValueError(f"Invalid NCT ID: {nct_id!r}")
        get_params = params or StudyGetParams()
        response = self._get(f"/studies/{nct_id}", get_params.to_query_params())
        return response.json()

    def iter_search_studies(
        self, params: StudiesSearchParams
    ) -> Iterator[dict[str, Any]]:
        collected = 0
        page_params = params.model_copy()

        while collected < self._pagination_cap:
            result = self.search_studies(page_params)
            for study in result.studies:
                yield study
                collected += 1
                if collected >= self._pagination_cap:
                    return

            if not result.next_page_token:
                return

            page_params = page_params.model_copy(
                update={"page_token": result.next_page_token}
            )


def ctgov_client_from_settings(settings: Settings) -> CtgovClient:
    return CtgovClient(
        base_url=settings.ctgov_base_url,
        timeout=settings.http_timeout,
        pagination_cap=settings.pagination_cap,
    )
