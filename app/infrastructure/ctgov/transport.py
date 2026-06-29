"""HTTP transport for ClinicalTrials.gov API (stdlib urllib).

ClinicalTrials.gov's WAF blocks httpx's TLS fingerprint; urllib works.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

USER_AGENT = "clinicaltrials-agent/0.1.0"
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
}


@dataclass(frozen=True)
class CtgovHttpResponse:
    status_code: int
    text: str

    def json(self) -> Any:
        return json.loads(self.text)


def urllib_get(
    base_url: str,
    path: str,
    params: dict[str, str],
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> CtgovHttpResponse:
    query = urllib.parse.urlencode(params)
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{query}"
    request = urllib.request.Request(
        url,
        headers={**DEFAULT_HEADERS, **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode()
            status_code = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        status_code = exc.code
    return CtgovHttpResponse(status_code=status_code, text=body)
