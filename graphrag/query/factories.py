# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Query Factory methods to support CLI."""

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from graphrag.config import (
    GraphRagConfig,
    LLMType,
)
from graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores import BaseVectorStore


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
    if config.llm.cognitive_services_endpoint is None:
        cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
    else:
        cognitive_services_endpoint = config.llm.cognitive_services_endpoint
    print(f"creating llm client with {llm_debug_info}")  # noqa T201
    return ChatOpenAI(
        api_key=config.llm.api_key,
        azure_ad_token_provider=get_bearer_token_provider(
            DefaultAzureCredential(), cognitive_services_endpoint
        )
        if is_azure_client and not config.llm.api_key
        else None,
        api_base=config.llm.api_base,
        model=config.llm.model,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=config.llm.deployment_name,
        api_version=config.llm.api_version,
        max_retries=config.llm.max_retries,
    )


def get_text_embedder(config: GraphRagConfig) -> OpenAIEmbedding:
    """Get the LLM client for embeddings."""
    is_azure_client = config.embeddings.llm.type == LLMType.AzureOpenAIEmbedding
    debug_embedding_api_key = config.embeddings.llm.api_key or ""
    llm_debug_info = {
        **config.embeddings.llm.model_dump(),
        "api_key": f"REDACTED,len={len(debug_embedding_api_key)}",
    }
    if config.embeddings.llm.cognitive_services_endpoint is None:
        cognitive_services_endpoint = "https://cognitiveservices.azure.com/.default"
    else:
        cognitive_services_endpoint = config.embeddings.llm.cognitive_services_endpoint
    print(f"creating embedding llm client with {llm_debug_info}")  # noqa T201
    return OpenAIEmbedding(
        api_key=config.embeddings.llm.api_key,
        azure_ad_token_provider=get_bearer_token_provider(
            DefaultAzureCredential(), cognitive_services_endpoint
        )
        if is_azure_client and not config.embeddings.llm.api_key
        else None,
        api_base=config.embeddings.llm.api_base,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        model=config.embeddings.llm.model,
        deployment_name=config.embeddings.llm.deployment_name,
        api_version=config.embeddings.llm.api_version,
        max_retries=config.embeddings.llm.max_retries,
    )


def get_local_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    text_units: list[TextUnit],
    entities: list[Entity],
    relationships: list[Relationship],
    covariates: dict[str, list[Covariate]],
    response_type: str,
    description_embedding_store: BaseVectorStore,
) -> LocalSearch:
    """Create a local search engine based on data + configuration."""
    llm = get_llm(config)
    text_embedder = get_text_embedder(config)
    token_encoder = tiktoken.get_encoding(config.encoding_model)

    ls_config = config.local_search

    return LocalSearch(
        llm=llm,
        context_builder=LocalSearchMixedContext(
            community_reports=reports,
            text_units=text_units,
            entities=entities,
            relationships=relationships,
            covariates=covariates,
            entity_text_embeddings=description_embedding_store,
            embedding_vectorstore_key=EntityVectorStoreKey.ID,  # if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
            text_embedder=text_embedder,
            token_encoder=token_encoder,
        ),
        token_encoder=token_encoder,
        llm_params={
            "max_tokens": ls_config.llm_max_tokens,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
            "temperature": 0.0,
        },
        context_builder_params={
            "text_unit_prop": ls_config.text_unit_prop,
            "community_prop": ls_config.community_prop,
            "conversation_history_max_turns": ls_config.conversation_history_max_turns,
            "conversation_history_user_turns_only": True,
            "top_k_mapped_entities": ls_config.top_k_entities,
            "top_k_relationships": ls_config.top_k_relationships,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
            "max_tokens": ls_config.max_tokens,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
        },
        response_type=response_type,
    )


def get_global_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    entities: list[Entity],
    response_type: str,
):
    """Create a global search engine based on data + configuration."""
    token_encoder = tiktoken.get_encoding(config.encoding_model)
    gs_config = config.global_search

    return GlobalSearch(
        llm=get_llm(config),
        context_builder=GlobalCommunityContext(
            community_reports=reports, entities=entities, token_encoder=token_encoder
        ),
        token_encoder=token_encoder,
        max_data_tokens=gs_config.data_max_tokens,
        map_llm_params={
            "max_tokens": gs_config.map_max_tokens,
            "temperature": gs_config.temperature,
            "top_p": gs_config.top_p,
        },
        reduce_llm_params={
            "max_tokens": gs_config.reduce_max_tokens,
            "temperature": gs_config.temperature,
            "top_p": gs_config.top_p,
        },
        allow_general_knowledge=False,
        json_mode=False,
        context_builder_params={
            "use_community_summary": False,
            "shuffle_data": True,
            "include_community_rank": True,
            "min_community_rank": 0,
            "community_rank_name": "rank",
            "include_community_weight": True,
            "community_weight_name": "occurrence weight",
            "normalize_community_weight": True,
            "max_tokens": gs_config.max_tokens,
            "context_name": "Reports",
        },
        concurrent_coroutines=gs_config.concurrency,
        response_type=response_type,
    )
