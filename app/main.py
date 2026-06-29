from fastapi import FastAPI

from app.core.config import Settings

settings = Settings()

app = FastAPI()
app.state.settings = settings


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
