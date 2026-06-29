from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = Field(..., min_length=1)
    ctgov_base_url: str = "https://clinicaltrials.gov/api/v2"
    http_timeout: float = 30.0
    pagination_cap: int = 1000
