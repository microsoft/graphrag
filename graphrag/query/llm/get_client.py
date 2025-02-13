# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Initialize LLM and Embedding clients."""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider

import graphrag.config.defaults as defs
from graphrag.config.enums import AuthType, LLMType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType


def get_llm(config: GraphRagConfig) -> ChatOpenAI:
    """Get the LLM client."""
    llm_config = config.get_language_model_config("default_chat_model")
    is_azure_client = llm_config.type == LLMType.AzureOpenAIChat
    debug_llm_key = llm_config.api_key or ""
    llm_debug_info = {
        **llm_config.model_dump(),
        "api_key": f"REDACTED,len={len(debug_llm_key)}",
    }
    audience = (
        llm_config.audience
        if llm_config.audience
        else "https://cognitiveservices.azure.com/.default"
    )
    print(f"creating llm client with {llm_debug_info}")  # noqa T201
    return ChatOpenAI(
        api_key=llm_config.api_key,
        azure_ad_token_provider=(
            get_bearer_token_provider(DefaultAzureCredential(), audience)
            if is_azure_client and llm_config.auth_type == AuthType.AzureManagedIdentity
            else None
        ),
        api_base=llm_config.api_base,
        organization=llm_config.organization,
        model=llm_config.model,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=llm_config.deployment_name,
        api_version=llm_config.api_version,
        max_retries=llm_config.max_retries
        if llm_config.max_retries != -1
        else defs.LLM_MAX_RETRIES,
        request_timeout=llm_config.request_timeout,
    )


def get_text_embedder(config: GraphRagConfig) -> OpenAIEmbedding:
    """Get the LLM client for embeddings."""
    embeddings_llm_config = config.get_language_model_config(config.embed_text.model_id)
    is_azure_client = embeddings_llm_config.type == LLMType.AzureOpenAIEmbedding
    debug_embedding_api_key = embeddings_llm_config.api_key or ""
    llm_debug_info = {
        **embeddings_llm_config.model_dump(),
        "api_key": f"REDACTED,len={len(debug_embedding_api_key)}",
    }
    if embeddings_llm_config.audience is None:
        audience = "https://cognitiveservices.azure.com/.default"
    else:
        audience = embeddings_llm_config.audience
    print(f"creating embedding llm client with {llm_debug_info}")  # noqa T201
    return OpenAIEmbedding(
        api_key=embeddings_llm_config.api_key,
        azure_ad_token_provider=(
            get_bearer_token_provider(DefaultAzureCredential(), audience)
            if is_azure_client
            and embeddings_llm_config.auth_type == AuthType.AzureManagedIdentity
            else None
        ),
        api_base=embeddings_llm_config.api_base,
        organization=embeddings_llm_config.organization,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        model=embeddings_llm_config.model,
        deployment_name=embeddings_llm_config.deployment_name,
        api_version=embeddings_llm_config.api_version,
        max_retries=embeddings_llm_config.max_retries
        if embeddings_llm_config.max_retries != -1
        else defs.LLM_MAX_RETRIES,
    )
