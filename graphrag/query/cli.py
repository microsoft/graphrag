# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Command line interface for the query module."""

import os
from pathlib import Path
from typing import cast

import pandas as pd
import tiktoken

from graphrag.config import (
    GlobalSearchConfig,
    GraphRagConfig,
    LLMType,
    LocalSearchConfig,
    create_graphrag_config,
)
from graphrag.index.progress import PrintProgressReporter
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.input.loaders.dfs import (
    store_entity_semantic_embeddings,
)
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
from graphrag.vector_stores.qdrant import Qdrant

from .indexer_adapters import (
    read_raw_covariates,
    read_raw_entities,
    read_raw_relationships,
    read_raw_reports,
    read_raw_text_units,
)

reporter = PrintProgressReporter("")


def __get_embedding_description_store():
    description_embedding_store = Qdrant(
        collection_name="entity_description_embeddings",
    )
    description_embedding_store.connect()

    return description_embedding_store


def __get_llm(config: GraphRagConfig):
    is_azure_client = (
        config.llm.type == LLMType.AzureOpenAIChat
        or config.llm.type == LLMType.AzureOpenAI
    )
    llm_debug_info = {
        **config.llm.model_dump(),
        "api_key": f"REDACTED,len={len(config.llm.api_key)}",
    }
    reporter.info(f"creating llm client with {llm_debug_info}")
    return ChatOpenAI(
        api_key=config.llm.api_key,
        api_base=config.llm.api_base,
        model=config.llm.model,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        deployment_name=config.llm.deployment_name,
        api_version=config.llm.api_version,
        max_retries=config.llm.max_retries,
    )


def __get_text_embedder(config: GraphRagConfig):
    is_azure_client = config.embeddings.llm.type == LLMType.AzureOpenAIEmbedding
    llm_debug_info = {
        **config.embeddings.llm.model_dump(),
        "api_key": f"REDACTED,len={len(config.embeddings.llm.api_key)}",
    }
    reporter.info(f"creating embedding llm client with {llm_debug_info}")
    return OpenAIEmbedding(
        api_key=config.embeddings.llm.api_key,
        api_base=config.embeddings.llm.api_base,
        api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
        model=config.embeddings.llm.model,
        deployment_name=config.embeddings.llm.deployment_name,
        api_version=config.embeddings.llm.api_version,
        max_retries=config.embeddings.llm.max_retries,
    )


def __get_local_search_engine(
    llm,
    token_encoder,
    reports,
    text_units,
    entities,
    relationships,
    covariates,
    description_embedding_store,
    text_embedder,
    response_type,
    config: LocalSearchConfig,
):
    context_builder = LocalSearchMixedContext(
        community_reports=reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        covariates=covariates,
        entity_text_embeddings=description_embedding_store,
        embedding_vectorstore_key=EntityVectorStoreKey.ID,  # if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
        text_embedder=text_embedder,
        token_encoder=token_encoder,
    )

    local_context_params = {
        "text_unit_prop": config.text_unit_prop,
        "community_prop": config.community_prop,
        "conversation_history_max_turns": config.conversation_history_max_turns,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": config.top_k_entities,
        "top_k_relationships": config.top_k_relationships,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": config.max_tokens,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
    }

    llm_params = {
        "max_tokens": config.llm_max_tokens,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
        "temperature": 0.0,
    }

    return LocalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=llm_params,
        context_builder_params=local_context_params,
        response_type=response_type,
    )


def __get_global_search_engine(
    llm, reports, token_encoder, response_type, config: GlobalSearchConfig
):
    context_builder = GlobalCommunityContext(
        community_reports=reports, token_encoder=token_encoder
    )

    context_builder_params = {
        "use_community_summary": False,
        "shuffle_data": True,
        "include_community_rank": True,
        "min_community_rank": 0,
        "max_tokens": config.max_tokens,
        "context_name": "Reports",
    }

    map_llm_params = {
        "max_tokens": config.map_max_tokens,
        "temperature": 0.0,
    }

    reduce_llm_params = {
        "max_tokens": config.reduce_max_tokens,
        "temperature": 0.0,
    }

    return GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        max_data_tokens=config.data_max_tokens,
        map_llm_params=map_llm_params,
        reduce_llm_params=reduce_llm_params,
        context_builder_params=context_builder_params,
        concurrent_coroutines=config.concurrency,
        response_type=response_type,
    )


def run_global_search(
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """Run a global search with the given query."""
    data_dir, root_dir, config = _configure_paths_and_settings(data_dir, root_dir)
    data_path = Path(data_dir)

    final_nodes: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_nodes.parquet"
    )
    final_community_reports: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )

    reports = read_raw_reports(final_community_reports, final_nodes, community_level)
    search_engine = __get_global_search_engine(
        llm=__get_llm(config),
        reports=reports,
        token_encoder=tiktoken.get_encoding("cl100k_base"),
        response_type=response_type,
        config=config.global_search,
    )

    result = search_engine.search(query=query)

    reporter.success(f"Global Search Response: {result.response}")
    return result.response


def run_local_search(
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """Run a local search with the given query."""
    data_dir, root_dir, config = _configure_paths_and_settings(data_dir, root_dir)
    data_path = Path(data_dir)

    final_nodes = pd.read_parquet(data_path / "create_final_nodes.parquet")
    final_community_reports = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )
    final_text_units = pd.read_parquet(data_path / "create_final_text_units.parquet")
    final_relationships = pd.read_parquet(
        data_path / "create_final_relationships.parquet"
    )
    final_nodes = pd.read_parquet(data_path / "create_final_nodes.parquet")
    final_entities = pd.read_parquet(data_path / "create_final_entities.parquet")
    final_covariates = pd.read_parquet(data_path / "create_final_covariates.parquet")

    description_embedding_store = __get_embedding_description_store()
    entities = read_raw_entities(final_nodes, final_entities, community_level)
    store_entity_semantic_embeddings(
        entities=entities, vectorstore=description_embedding_store
    )
    covariates = read_raw_covariates(final_covariates)

    search_engine = __get_local_search_engine(
        llm=__get_llm(config),
        token_encoder=tiktoken.get_encoding("cl100k_base"),
        reports=read_raw_reports(final_community_reports, final_nodes, community_level),
        text_units=read_raw_text_units(final_text_units),
        entities=entities,
        relationships=read_raw_relationships(final_relationships, entities),
        covariates={"claims": covariates},
        description_embedding_store=description_embedding_store,
        text_embedder=__get_text_embedder(config),
        response_type=response_type,
        config=config.local_search,
    )

    result = search_engine.search(query=query)
    reporter.success(f"Local Search Response: {result.response}")
    return result.response


def _configure_paths_and_settings(
    data_dir: str | None, root_dir: str | None
) -> tuple[str, str | None, GraphRagConfig]:
    if data_dir is None and root_dir is None:
        msg = "Either data_dir or root_dir must be provided."
        raise ValueError(msg)
    if data_dir is None:
        data_dir = _infer_data_dir(cast(str, root_dir))
    config = _create_graphrag_config(root_dir, data_dir)
    return data_dir, root_dir, config


def _infer_data_dir(root: str) -> str:
    output = Path(root) / "output"
    # use the latest data-run folder
    if output.exists():
        folders = sorted(output.iterdir(), key=os.path.getmtime, reverse=True)
        if len(folders) > 0:
            folder = folders[0]
            return str((folder / "artifacts").absolute())
    msg = f"Could not infer data directory from root={root}"
    raise ValueError(msg)


def _create_graphrag_config(root: str | None, data_dir: str | None) -> GraphRagConfig:
    """Create a GraphRag configuration."""
    return _read_config_parameters(cast(str, root or data_dir))


def _read_config_parameters(root: str):
    _root = Path(root)
    settings_yaml = _root / "settings.yaml"
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"
    settings_json = _root / "settings.json"

    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("r") as file:
            import yaml

            data = yaml.safe_load(file)
            return create_graphrag_config(data, root)

    if settings_json.exists():
        reporter.info(f"Reading settings from {settings_json}")
        with settings_json.open("r") as file:
            import json

            data = json.loads(file.read())
            return create_graphrag_config(data, root)

    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
