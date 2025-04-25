# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Query Factory methods to support CLI."""

import tiktoken

from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.data_model.covariate import Covariate
from graphrag.data_model.entity import Entity
from graphrag.data_model.relationship import Relationship
from graphrag.data_model.text_unit import TextUnit
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.providers.fnllm.utils import (
    get_openai_model_parameters_from_config,
)
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.structured_search.basic_search.basic_context import (
    BasicSearchContext,
)
from graphrag.query.structured_search.basic_search.search import BasicSearch
from graphrag.query.structured_search.drift_search.drift_context import (
    DRIFTSearchContextBuilder,
)
from graphrag.query.structured_search.drift_search.search import DRIFTSearch
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.base import BaseVectorStore


def get_local_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    text_units: list[TextUnit],
    entities: list[Entity],
    relationships: list[Relationship],
    covariates: dict[str, list[Covariate]],
    response_type: str,
    description_embedding_store: BaseVectorStore,
    system_prompt: str | None = None,
    callbacks: list[QueryCallbacks] | None = None,
) -> LocalSearch:
    """Create a local search engine based on data + configuration."""
    model_settings = config.get_language_model_config(config.local_search.chat_model_id)

    if model_settings.max_retries == -1:
        model_settings.max_retries = (
            len(reports) + len(entities) + len(relationships) + len(covariates)
        )

    chat_model = ModelManager().get_or_create_chat_model(
        name="local_search_chat",
        model_type=model_settings.type,
        config=model_settings,
    )

    embedding_settings = config.get_language_model_config(
        config.local_search.embedding_model_id
    )
    if embedding_settings.max_retries == -1:
        embedding_settings.max_retries = (
            len(reports) + len(entities) + len(relationships)
        )
    embedding_model = ModelManager().get_or_create_embedding_model(
        name="local_search_embedding",
        model_type=embedding_settings.type,
        config=embedding_settings,
    )

    token_encoder = tiktoken.get_encoding(model_settings.encoding_model)

    ls_config = config.local_search

    model_params = get_openai_model_parameters_from_config(model_settings)

    return LocalSearch(
        model=chat_model,
        system_prompt=system_prompt,
        context_builder=LocalSearchMixedContext(
            community_reports=reports,
            text_units=text_units,
            entities=entities,
            relationships=relationships,
            covariates=covariates,
            entity_text_embeddings=description_embedding_store,
            embedding_vectorstore_key=EntityVectorStoreKey.ID,  # if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
            text_embedder=embedding_model,
            token_encoder=token_encoder,
        ),
        token_encoder=token_encoder,
        model_params=model_params,
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
            "max_context_tokens": ls_config.max_context_tokens,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
        },
        response_type=response_type,
        callbacks=callbacks,
    )


def get_global_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    entities: list[Entity],
    communities: list[Community],
    response_type: str,
    dynamic_community_selection: bool = False,
    map_system_prompt: str | None = None,
    reduce_system_prompt: str | None = None,
    general_knowledge_inclusion_prompt: str | None = None,
    callbacks: list[QueryCallbacks] | None = None,
) -> GlobalSearch:
    """Create a global search engine based on data + configuration."""
    model_settings = config.get_language_model_config(
        config.global_search.chat_model_id
    )

    if model_settings.max_retries == -1:
        model_settings.max_retries = len(reports) + len(entities)
    model = ModelManager().get_or_create_chat_model(
        name="global_search",
        model_type=model_settings.type,
        config=model_settings,
    )

    model_params = get_openai_model_parameters_from_config(model_settings)

    # Here we get encoding based on specified encoding name
    token_encoder = tiktoken.get_encoding(model_settings.encoding_model)
    gs_config = config.global_search

    dynamic_community_selection_kwargs = {}
    if dynamic_community_selection:
        # TODO: Allow for another llm definition only for Global Search to leverage -mini models

        dynamic_community_selection_kwargs.update({
            "model": model,
            "token_encoder": token_encoder,
            "keep_parent": gs_config.dynamic_search_keep_parent,
            "num_repeats": gs_config.dynamic_search_num_repeats,
            "use_summary": gs_config.dynamic_search_use_summary,
            "concurrent_coroutines": model_settings.concurrent_requests,
            "threshold": gs_config.dynamic_search_threshold,
            "max_level": gs_config.dynamic_search_max_level,
            "model_params": {**model_params},
        })

    return GlobalSearch(
        model=model,
        map_system_prompt=map_system_prompt,
        reduce_system_prompt=reduce_system_prompt,
        general_knowledge_inclusion_prompt=general_knowledge_inclusion_prompt,
        context_builder=GlobalCommunityContext(
            community_reports=reports,
            communities=communities,
            entities=entities,
            token_encoder=token_encoder,
            dynamic_community_selection=dynamic_community_selection,
            dynamic_community_selection_kwargs=dynamic_community_selection_kwargs,
        ),
        token_encoder=token_encoder,
        max_data_tokens=gs_config.data_max_tokens,
        map_llm_params={**model_params},
        reduce_llm_params={**model_params},
        map_max_length=gs_config.map_max_length,
        reduce_max_length=gs_config.reduce_max_length,
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
            "max_context_tokens": gs_config.max_context_tokens,
            "context_name": "Reports",
        },
        concurrent_coroutines=model_settings.concurrent_requests,
        response_type=response_type,
        callbacks=callbacks,
    )


def get_drift_search_engine(
    config: GraphRagConfig,
    reports: list[CommunityReport],
    text_units: list[TextUnit],
    entities: list[Entity],
    relationships: list[Relationship],
    description_embedding_store: BaseVectorStore,
    response_type: str,
    local_system_prompt: str | None = None,
    reduce_system_prompt: str | None = None,
    callbacks: list[QueryCallbacks] | None = None,
) -> DRIFTSearch:
    """Create a local search engine based on data + configuration."""
    chat_model_settings = config.get_language_model_config(
        config.drift_search.chat_model_id
    )

    if chat_model_settings.max_retries == -1:
        chat_model_settings.max_retries = (
            config.drift_search.drift_k_followups
            * config.drift_search.primer_folds
            * config.drift_search.n_depth
        )

    chat_model = ModelManager().get_or_create_chat_model(
        name="drift_search_chat",
        model_type=chat_model_settings.type,
        config=chat_model_settings,
    )

    embedding_model_settings = config.get_language_model_config(
        config.drift_search.embedding_model_id
    )

    if embedding_model_settings.max_retries == -1:
        embedding_model_settings.max_retries = (
            len(reports) + len(entities) + len(relationships)
        )

    embedding_model = ModelManager().get_or_create_embedding_model(
        name="drift_search_embedding",
        model_type=embedding_model_settings.type,
        config=embedding_model_settings,
    )

    token_encoder = tiktoken.get_encoding(chat_model_settings.encoding_model)

    return DRIFTSearch(
        model=chat_model,
        context_builder=DRIFTSearchContextBuilder(
            model=chat_model,
            text_embedder=embedding_model,
            entities=entities,
            relationships=relationships,
            reports=reports,
            entity_text_embeddings=description_embedding_store,
            text_units=text_units,
            local_system_prompt=local_system_prompt,
            reduce_system_prompt=reduce_system_prompt,
            config=config.drift_search,
            response_type=response_type,
        ),
        token_encoder=token_encoder,
        callbacks=callbacks,
    )


def get_basic_search_engine(
    text_units: list[TextUnit],
    text_unit_embeddings: BaseVectorStore,
    config: GraphRagConfig,
    system_prompt: str | None = None,
    response_type: str = "multiple paragraphs",
    callbacks: list[QueryCallbacks] | None = None,
) -> BasicSearch:
    """Create a basic search engine based on data + configuration."""
    chat_model_settings = config.get_language_model_config(
        config.basic_search.chat_model_id
    )

    if chat_model_settings.max_retries == -1:
        chat_model_settings.max_retries = len(text_units)

    chat_model = ModelManager().get_or_create_chat_model(
        name="basic_search_chat",
        model_type=chat_model_settings.type,
        config=chat_model_settings,
    )

    embedding_model_settings = config.get_language_model_config(
        config.basic_search.embedding_model_id
    )
    if embedding_model_settings.max_retries == -1:
        embedding_model_settings.max_retries = len(text_units)

    embedding_model = ModelManager().get_or_create_embedding_model(
        name="basic_search_embedding",
        model_type=embedding_model_settings.type,
        config=embedding_model_settings,
    )

    token_encoder = tiktoken.get_encoding(chat_model_settings.encoding_model)

    bs_config = config.basic_search

    model_params = get_openai_model_parameters_from_config(chat_model_settings)

    return BasicSearch(
        model=chat_model,
        system_prompt=system_prompt,
        response_type=response_type,
        context_builder=BasicSearchContext(
            text_embedder=embedding_model,
            text_unit_embeddings=text_unit_embeddings,
            text_units=text_units,
            token_encoder=token_encoder,
        ),
        token_encoder=token_encoder,
        model_params=model_params,
        context_builder_params={
            "embedding_vectorstore_key": "id",
            "k": bs_config.k,
            "max_context_tokens": bs_config.max_context_tokens,
        },
        callbacks=callbacks,
    )
