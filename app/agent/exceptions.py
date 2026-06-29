"""Agent-layer errors surfaced to callers (HTTP mapping in Stage 9)."""


class AgentError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
