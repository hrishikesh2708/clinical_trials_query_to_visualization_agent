from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.v1 import router as v1_router
from app.core.config import Settings

settings = Settings()

app = FastAPI()
app.state.settings = settings

register_exception_handlers(app)
app.include_router(v1_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
