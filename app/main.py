from fastapi import FastAPI, HTTPException

from app.core.config import Settings
from app.core.schemas.request import VisualizeRequest
from app.core.schemas.response import VisualizeResponse

settings = Settings()

app = FastAPI()
app.state.settings = settings


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/visualize",
    response_model=VisualizeResponse,
    status_code=501,
    tags=["visualize"],
)
def visualize_stub(_: VisualizeRequest) -> VisualizeResponse:
    raise HTTPException(status_code=501, detail="Not implemented until Stage 9")
