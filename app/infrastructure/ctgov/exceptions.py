class CtgovApiError(Exception):
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"ClinicalTrials.gov API error {status_code}: {body}")


class CtgovRateLimitError(CtgovApiError):
    pass
