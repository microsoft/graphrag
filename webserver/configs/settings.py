import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_port: int = 20213
    data: str = (
        "/Users/evilkylin/Projects/graphrag/output"
    )
    lancedb_uri: str = (
        "/Users/evilkylin/Projects/graphrag/lancedb"  # f"{input_dir}/lancedb"
    )
    api_key: str = os.environ.get("DEEP_SEEK_API_KEY")
    api_base: str = "https://api.deepseek.com/v1"
    api_version: str = ""
    api_type: str = ""
    llm_model: str = "deepseek-chat"
    max_retries: int = 3
    embedding_model: str = "text-embedding-ada-002"
    embedding_api_base: str = "http://localhost:1234/v1"
    max_tokens: int = 4096
    temperature: float = 0.0
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None


settings = Settings()
