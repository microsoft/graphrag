# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Initialize LLM and Embedding clients."""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from graphrag.config.enums import LLMType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType


def get_llm(config: GraphRagConfig) -> ChatOpenAI:
    """Get the LLM client."""
    is_azure_client = (
        config.llm.type == LLMType.AzureOpenAIChat
        or config.llm.type == LLMType.AzureOpenAI
    )
    debug_llm_key = config.llm.api_key or ""
    llm_debug_info = {
        **config.llm.model_dump(),
        "api_key": f"REDACTED,len={len(debug_llm_key)}",
    }
    audience = (
        config.llm.audience
        if config.llm.audience
        else "https://cognitiveservices.azure.com/.default"
    )
    print(f"creating llm client with {llm_debug_info}")  # noqa T201
    return ChatOpenAI(
        api_key=config.llm.api_key,
        azure_ad_token_provider=(
            get_bearer_token_provider(DefaultAzureCredential(), audience)
            if is_azure_client and not config.llm.api_key
            else None
        ),
        api_base=config.llm.api_base,
        organization=config.llm.organization,
        model=config.llm.model,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=config.llm.deployment_name,
        api_version=config.llm.api_version,
        max_retries=config.llm.max_retries,
        request_timeout=config.llm.request_timeout,
    )


def get_text_embedder(config: GraphRagConfig) -> OpenAIEmbedding:
    """Get the LLM client for embeddings."""
    is_azure_client = config.embeddings.llm.type == LLMType.AzureOpenAIEmbedding
    debug_embedding_api_key = config.embeddings.llm.api_key or ""
    llm_debug_info = {
        **config.embeddings.llm.model_dump(),
        "api_key": f"REDACTED,len={len(debug_embedding_api_key)}",
    }
    if config.embeddings.llm.audience is None:
        audience = "https://cognitiveservices.azure.com/.default"
    else:
        audience = config.embeddings.llm.audience
    print(f"creating embedding llm client with {llm_debug_info}")  # noqa T201
    return OpenAIEmbedding(
        api_key=config.embeddings.llm.api_key,
        azure_ad_token_provider=(
            get_bearer_token_provider(DefaultAzureCredential(), audience)
            if is_azure_client and not config.embeddings.llm.api_key
            else None
        ),
        api_base=config.embeddings.llm.api_base,
        organization=config.llm.organization,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        model=config.embeddings.llm.model,
        deployment_name=config.embeddings.llm.deployment_name,
        api_version=config.embeddings.llm.api_version,
        max_retries=config.embeddings.llm.max_retries,
    )
