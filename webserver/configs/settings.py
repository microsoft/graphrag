import os

import yaml
from azure.identity import get_bearer_token_provider, DefaultAzureCredential
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from graphrag.config import LLMParameters, TextEmbeddingConfig, LocalSearchConfig, GlobalSearchConfig, LLMType
from graphrag.query.llm.oai import OpenaiApiType


class Settings(BaseSettings):
    server_port: int = 20213
    website_address: str = f"http://127.0.0.1:{server_port}"
    cors_allowed_origins: list = ["*"] # Edit the list to restrict access.
    data: str = (
        "./output"
    )
    lancedb_uri: str = (
        "./lancedb"
    )
    llm: LLMParameters
    embeddings: TextEmbeddingConfig
    global_search: GlobalSearchConfig
    local_search: LocalSearchConfig
    encoding_model: str = "cl100k_base"

    def is_azure_client(self):
        return self.llm.type == LLMType.AzureOpenAIChat or settings.llm.type == LLMType.AzureOpenAI

    def get_api_type(self):
        return OpenaiApiType.AzureOpenAI if self.is_azure_client() else OpenaiApiType.OpenAI

    def azure_ad_token_provider(self):
        if self.llm.cognitive_services_endpoint is None:
            cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
        else:
            cognitive_services_endpoint = settings.llm.cognitive_services_endpoint
        if self.is_azure_client() and not settings.llm.api_key:
            return get_bearer_token_provider(DefaultAzureCredential(), cognitive_services_endpoint)
        else:
            return None


def load_settings_from_yaml(file_path: str) -> Settings:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    llm_config = config['llm']
    embeddings_config = config['embeddings']
    global_search_config = config['global_search']
    local_search_config = config['local_search']
    encoding_model = config['encoding_model']

    # Manually setting the API keys from environment variables if specified
    load_dotenv()
    llm_params = LLMParameters(**llm_config)
    llm_params.api_key = os.environ.get("GRAPHRAG_API_KEY", llm_config['api_key'])
    text_embedding = TextEmbeddingConfig(**embeddings_config)
    text_embedding.llm.api_key = os.environ.get("GRAPHRAG_API_KEY", embeddings_config['llm']['api_key'])

    return Settings(
        llm=llm_params,
        embeddings=text_embedding,
        global_search=GlobalSearchConfig(**global_search_config if global_search_config else {}),
        local_search=LocalSearchConfig(**local_search_config if local_search_config else {}),
        encoding_model=encoding_model
    )


settings = load_settings_from_yaml("settings.yaml")
