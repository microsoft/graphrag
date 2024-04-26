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
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
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

reporter = PrintProgressReporter("")


def __get_reports(data_dir: Path, community_level: int):
    entity_df: pd.DataFrame = pd.read_parquet(data_dir / "create_final_nodes.parquet")
    entity_df = cast(
        pd.DataFrame,
        entity_df[
            (entity_df.type == "entity")
            & (entity_df.level <= f"level_{community_level}")
        ],
    )
    entity_df["community"] = entity_df["community"].fillna(-1)
    entity_df["community"] = entity_df["community"].astype(int)

    entity_df = entity_df.groupby(["title"]).agg({"community": "max"}).reset_index()
    entity_df["community"] = entity_df["community"].astype(str)
    filtered_community_df = entity_df.rename(columns={"community": "community_id"})[
        "community_id"
    ].drop_duplicates()

    report_df: pd.DataFrame = pd.read_parquet(
        data_dir / "create_final_community_reports.parquet"
    )
    report_df = cast(
        pd.DataFrame, report_df[report_df.level <= f"level_{community_level}"]
    )

    report_df["rank"] = report_df["rank"].fillna(-1)
    report_df["rank"] = report_df["rank"].astype(int)

    report_df = report_df.merge(filtered_community_df, on="community_id", how="inner")

    return read_community_reports(
        df=report_df,
        id_col="community_id",
        short_id_col="community_id",
        community_col="community_id",
        title_col="title",
        summary_col="summary",
        content_col="full_content",
        rank_col="rank",
        summary_embedding_col=None,
        content_embedding_col=None,
    )


def __get_embedding_description_store():
    description_embedding_store = Qdrant(
        collection_name="entity_description_embeddings",
    )
    description_embedding_store.connect()

    return description_embedding_store


def __get_entities(
    data_dir: Path, community_level: int, description_embedding_store: Qdrant
):
    entity_df: pd.DataFrame = pd.read_parquet(data_dir / "create_final_nodes.parquet")
    entity_df = cast(
        pd.DataFrame,
        entity_df[entity_df.level <= f"level_{community_level}"],
    )
    entity_df = cast(pd.DataFrame, entity_df[["title", "degree", "community"]]).rename(
        columns={"title": "name", "degree": "rank"}
    )

    entity_df["community"] = entity_df["community"].fillna(-1)
    entity_df["community"] = entity_df["community"].astype(int)
    entity_df["rank"] = entity_df["rank"].astype(int)

    # for duplicate entities, keep the one with the highest community level
    entity_df = (
        entity_df.groupby(["name", "rank"]).agg({"community": "max"}).reset_index()
    )
    entity_df["community"] = entity_df["community"].apply(lambda x: [str(x)])

    entity_embedding_df = pd.read_parquet(data_dir / "create_final_entities.parquet")
    entity_embedding_df = entity_embedding_df[
        [
            "id",
            "human_readable_id",
            "name",
            "type",
            "description",
            "description_embedding",
            "text_unit_ids",
        ]
    ]

    entity_df = entity_df.merge(
        entity_embedding_df, on="name", how="inner"
    ).drop_duplicates(subset=["name"])

    # read entity dataframe to knowledge model objects
    entities = read_entities(
        df=entity_df,
        id_col="id",
        title_col="name",
        type_col="type",
        short_id_col="human_readable_id",
        description_col="description",
        community_col="community",
        rank_col="rank",
        name_embedding_col=None,
        description_embedding_col="description_embedding",
        graph_embedding_col=None,
        text_unit_ids_col="text_unit_ids",
        document_ids_col=None,
    )
    store_entity_semantic_embeddings(
        entities=entities, vectorstore=description_embedding_store
    )
    return entities


def __get_relationships(data_dir: Path):
    relationship_df: pd.DataFrame = pd.read_parquet(
        data_dir / "create_final_relationships.parquet"
    )

    return read_relationships(
        df=relationship_df,
        short_id_col="human_readable_id",
        description_embedding_col=None,
        document_ids_col=None,
        attributes_cols=["rank"],
    )


def __get_claims(data_dir: Path):
    try:
        covariate_df: pd.DataFrame = pd.read_parquet(
            data_dir / "create_final_covariates.parquet"
        )
        covariate_df = cast(
            pd.DataFrame,
            covariate_df[
                [
                    "id",
                    "human_readable_id",
                    "type",
                    "subject_id",
                    "subject_type",
                    "object_id",
                    "status",
                    "start_date",
                    "end_date",
                    "description",
                ]
            ],
        )

    except:  # noqa: E722
        columns = [
            "id",
            "human_readable_id",
            "type",
            "subject_id",
            "object_id",
            "status",
            "start_date",
            "end_date",
            "description",
        ]
        covariate_df = pd.DataFrame({column: [] for column in columns})
    covariate_df["id"] = covariate_df["id"].astype(str)
    covariate_df["human_readable_id"] = covariate_df["human_readable_id"].astype(str)

    claims = read_covariates(
        df=covariate_df,
        id_col="id",
        short_id_col="human_readable_id",
        subject_col="subject_id",
        subject_type_col=None,
        covariate_type_col="type",
        attributes_cols=[
            "object_id",
            "status",
            "start_date",
            "end_date",
            "description",
        ],
        text_unit_ids_col=None,
        document_ids_col=None,
    )
    return {"claims": claims}


def __get_text_units(data_dir: Path):
    text_unit_df = pd.read_parquet(data_dir / "create_final_text_units.parquet")

    return read_text_units(
        df=text_unit_df,
        id_col="id",
        short_id_col=None,
        text_col="text",
        embedding_col="text_embedding",
        entities_col=None,
        relationships_col=None,
        covariates_col=None,
    )


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
    reports = __get_reports(data_dir=Path(data_dir), community_level=community_level)
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
    description_embedding_store = __get_embedding_description_store()
    entities = __get_entities(
        data_dir=Path(data_dir),
        community_level=community_level,
        description_embedding_store=description_embedding_store,
    )

    search_engine = __get_local_search_engine(
        llm=__get_llm(config),
        token_encoder=tiktoken.get_encoding("cl100k_base"),
        reports=__get_reports(data_dir=Path(data_dir), community_level=community_level),
        text_units=__get_text_units(data_dir=Path(data_dir)),
        entities=entities,
        relationships=__get_relationships(data_dir=Path(data_dir)),
        covariates=__get_claims(data_dir=Path(data_dir)),
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
