# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Command line interface for the query module."""

import os
from pathlib import Path
from typing import cast

import pandas as pd
import tiktoken

from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.input.loaders.dfs import (
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
    store_entity_semantic_embeddings,
)
from graphrag.query.input.retrieval.relationships import (
    calculate_relationship_combined_rank,
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

_DEFAULT_LLM_MODEL = "gpt-4-turbo-preview"
_DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _env_with_fallback(key: str, fallback: list[str]):
    for k in [key, *fallback]:
        if k in os.environ:
            return os.environ[k]
    msg = f"None of the following environment variables found: {key}, {fallback}"
    raise ValueError(msg)


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
        entity_df[
            (entity_df.type == "entity")
            & (entity_df.level <= f"level_{community_level}")
        ],
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


def __get_relationships(data_dir: Path, entities):
    relationship_df: pd.DataFrame = pd.read_parquet(
        data_dir / "create_final_relationships.parquet"
    )
    relationship_df = cast(
        pd.DataFrame,
        relationship_df[
            [
                "id",
                "human_readable_id",
                "source",
                "target",
                "description",
                "weight",
                "text_unit_ids",
            ]
        ],
    )
    relationship_df["id"] = relationship_df["id"].astype(str)
    relationship_df["human_readable_id"] = relationship_df["human_readable_id"].astype(
        str
    )
    relationship_df["weight"] = relationship_df["weight"].astype(float)
    relationship_df["text_unit_ids"] = relationship_df["text_unit_ids"].apply(
        lambda x: x.split(",")
    )

    relationships = read_relationships(
        df=relationship_df,
        id_col="id",
        short_id_col="human_readable_id",
        source_col="source",
        target_col="target",
        description_col="description",
        weight_col="weight",
        description_embedding_col=None,
        text_unit_ids_col="text_unit_ids",
        document_ids_col=None,
    )
    return calculate_relationship_combined_rank(
        relationships=relationships, entities=entities, ranking_attribute="rank"
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


def __get_llm():
    return ChatOpenAI(
        api_key=_env_with_fallback(
            "GRAPHRAG_LLM_API_KEY", ["GRAPHRAG_API_KEY", "OPENAI_API_KEY"]
        ),
        api_base=_env_with_fallback("GRAPHRAG_LLM_API_BASE", ["GRAPHRAG_API_BASE"]),
        model=os.environ.get("GRAPHRAG_LLM_MODEL", _DEFAULT_LLM_MODEL),
        api_type=OpenaiApiType.OpenAI
        if os.environ.get("GRAPHRAG_LLM_TYPE", "openai_chat") == "openai_chat"
        else OpenaiApiType.AzureOpenAI,
        deployment_name=os.environ.get(
            "GRAPHRAG_LLM_DEPLOYMENT_NAME", _DEFAULT_LLM_MODEL
        ),
        api_version=_env_with_fallback(
            "GRAPHRAG_LLM_API_VERSION", ["GRAPHRAG_API_VERSION", "OPENAI_API_VERSION"]
        ),
        max_retries=int(os.environ.get("GRAPHRAG_LLM_MAX_RETRIES", 20)),
    )


def __get_text_embedder():
    return OpenAIEmbedding(
        api_key=_env_with_fallback(
            "GRAPHRAG_EMBEDDING_API_KEY", ["GRAPHRAG_API_KEY", "OPENAI_API_KEY"]
        ),
        api_base=_env_with_fallback(
            "GRAPHRAG_EMBEDDING_API_BASE", ["GRAPHRAG_API_BASE"]
        ),
        api_type=OpenaiApiType.OpenAI
        if os.environ.get("GRAPHRAG_EMBEDDING_TYPE", "openai_embedding")
        == "openai_embedding"
        else OpenaiApiType.AzureOpenAI,
        model=os.environ.get("GRAPHRAG_EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL),
        deployment_name=os.environ.get(
            "GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME", _DEFAULT_EMBEDDING_MODEL
        ),
        api_version=_env_with_fallback(
            "GRAPHRAG_EMBEDDING_API_VERSION",
            ["GRAPHRAG_API_VERSION", "OPENAI_API_VERSION"],
        ),
        max_retries=int(os.environ.get("GRAPHRAG_EMBEDDING_MAX_RETRIES", 20)),
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
        "text_unit_prop": float(os.environ.get("TEXT_UNIT_PROP", 0.5)),
        "community_prop": float(os.environ.get("COMMUNITY_PROP", 0.1)),
        "conversation_history_max_turns": int(
            os.environ.get("CONVERSATION_HISTORY_MAX_TURNS", 5)
        ),
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": int(os.environ.get("TOP_K_MAPPED_ENTITIES", 10)),
        "top_k_relationships": int(os.environ.get("TOP_K_RELATIONSHIPS", 10)),
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": int(
            os.environ.get("LOCAL_CONTEXT_MAX_TOKENS", 12000)
        ),  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
    }

    llm_params = {
        "max_tokens": int(
            os.environ.get("GRAPHRAG_LLM_MAX_TOKENS", 2000)
        ),  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
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


def __get_global_search_engine(llm, reports, token_encoder, response_type):
    context_builder = GlobalCommunityContext(
        community_reports=reports, token_encoder=token_encoder
    )

    context_builder_params = {
        "use_community_summary": False,
        "shuffle_data": True,
        "include_community_rank": True,
        "min_community_rank": 0,
        "max_tokens": os.environ.get("CONTEXT_BUILDER_MAX_TOKENS", 12000),
        "context_name": "Reports",
    }

    map_llm_params = {
        "max_tokens": os.environ.get("MAP_LLM_MAX_TOKENS", 500),
        "temperature": 0.0,
    }

    reduce_llm_params = {
        "max_tokens": os.environ.get("REDUCE_LLM_MAX_TOKENS", 2000),
        "temperature": 0.0,
    }

    return GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        max_data_tokens=int(os.environ.get("SEARCH_ENGINE_MAX_TOKENS", 12000)),
        map_llm_params=map_llm_params,
        reduce_llm_params=reduce_llm_params,
        context_builder_params=context_builder_params,
        concurrent_coroutines=int(os.environ.get("SEARCH_ENGINE_CONCURRENCY", 32)),
        response_type=response_type,
    )


def run_global_search(
    data_dir: str, community_level: int, response_type: str, query: str
):
    """Run a global search with the given query."""
    reports = __get_reports(data_dir=Path(data_dir), community_level=community_level)
    search_engine = __get_global_search_engine(
        llm=__get_llm(),
        reports=reports,
        token_encoder=tiktoken.get_encoding("cl100k_base"),
        response_type=response_type,
    )

    result = search_engine.search(query=query)

    print(result.response)  # noqa: T201
    return result.response


def run_local_search(
    data_dir: str, community_level: int, response_type: str, query: str
):
    """Run a local search with the given query."""
    description_embedding_store = __get_embedding_description_store()
    entities = __get_entities(
        data_dir=Path(data_dir),
        community_level=community_level,
        description_embedding_store=description_embedding_store,
    )

    search_engine = __get_local_search_engine(
        llm=__get_llm(),
        token_encoder=tiktoken.get_encoding("cl100k_base"),
        reports=__get_reports(data_dir=Path(data_dir), community_level=community_level),
        text_units=__get_text_units(data_dir=Path(data_dir)),
        entities=entities,
        relationships=__get_relationships(data_dir=Path(data_dir), entities=entities),
        covariates=__get_claims(data_dir=Path(data_dir)),
        description_embedding_store=description_embedding_store,
        text_embedder=__get_text_embedder(),
        response_type=response_type,
    )

    result = search_engine.search(query=query)
    print(result.response)  # noqa: T201
    return result.response
