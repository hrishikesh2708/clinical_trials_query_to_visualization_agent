from collections.abc import Iterator
from typing import Any

import httpx

from app.core.config import Settings
from app.infrastructure.ctgov.exceptions import CtgovApiError, CtgovRateLimitError
from app.infrastructure.ctgov.models import StudiesSearchParams, StudiesSearchResult


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

    def search_studies(self, params: StudiesSearchParams) -> StudiesSearchResult:
        url = f"{self._base_url}/studies"
        query_params = params.to_query_params()

        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url, params=query_params)

        if response.status_code == 429:
            raise CtgovRateLimitError(response.status_code, response.text)
        if response.status_code >= 400:
            raise CtgovApiError(response.status_code, response.text)

        data = response.json()
        return StudiesSearchResult(
            studies=data.get("studies", []),
            next_page_token=data.get("nextPageToken"),
            total_count=data.get("totalCount"),
        )

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
