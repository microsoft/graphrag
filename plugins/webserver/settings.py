import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_port: int = 20213
    data: str = (
        "./context"
    )
    lancedb_uri: str = (
        "./lancedb"
    )
    api_key: str = 'sk-1VVNBnoziKaOfF978cEc44C85aBa405882C8503327692156'
    api_base: str = "https://aihubmix.com/v1/"
    api_version: str = ""
    api_type: str = ""
    llm_model: str = "gpt-4o"
    max_retries: int = 3
    embedding_model: str = "text-embedding-3-small"
    embedding_api_base: str = "https://aihubmix.com/v1/"
    context_max_tokens: int = 24000
    response_max_tokens:int = 4096

    temperature: float = 0.0
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None


settings = Settings()
