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
    default_llm_settings = config.get_language_model_config("default_chat_model")
    is_azure_client = default_llm_settings.type == LLMType.AzureOpenAIChat
    debug_llm_key = default_llm_settings.api_key or ""
    llm_debug_info = {
        **default_llm_settings.model_dump(),
        "api_key": f"REDACTED,len={len(debug_llm_key)}",
    }
    audience = (
        default_llm_settings.audience
        if default_llm_settings.audience
        else "https://cognitiveservices.azure.com/.default"
    )
    print(f"creating llm client with {llm_debug_info}")  # noqa T201
    return ChatOpenAI(
        api_key=default_llm_settings.api_key,
        azure_ad_token_provider=(
            get_bearer_token_provider(DefaultAzureCredential(), audience)
            if is_azure_client and not default_llm_settings.api_key
            else None
        ),
        api_base=default_llm_settings.api_base,
        organization=default_llm_settings.organization,
        model=default_llm_settings.model,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=default_llm_settings.deployment_name,
        api_version=default_llm_settings.api_version,
        max_retries=default_llm_settings.max_retries,
        request_timeout=default_llm_settings.request_timeout,
    )


def get_text_embedder(config: GraphRagConfig) -> OpenAIEmbedding:
    """Get the LLM client for embeddings."""
    embeddings_llm_settings = config.get_language_model_config(
        config.embeddings.model_id
    )
    is_azure_client = embeddings_llm_settings.type == LLMType.AzureOpenAIEmbedding
    debug_embedding_api_key = embeddings_llm_settings.api_key or ""
    llm_debug_info = {
        **embeddings_llm_settings.model_dump(),
        "api_key": f"REDACTED,len={len(debug_embedding_api_key)}",
    }
    if embeddings_llm_settings.audience is None:
        audience = "https://cognitiveservices.azure.com/.default"
    else:
        audience = embeddings_llm_settings.audience
    print(f"creating embedding llm client with {llm_debug_info}")  # noqa T201
    return OpenAIEmbedding(
        api_key=embeddings_llm_settings.api_key,
        azure_ad_token_provider=(
            get_bearer_token_provider(DefaultAzureCredential(), audience)
            if is_azure_client and not embeddings_llm_settings.api_key
            else None
        ),
        api_base=embeddings_llm_settings.api_base,
        organization=embeddings_llm_settings.organization,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        model=embeddings_llm_settings.model,
        deployment_name=embeddings_llm_settings.deployment_name,
        api_version=embeddings_llm_settings.api_version,
        max_retries=embeddings_llm_settings.max_retries,
    )
