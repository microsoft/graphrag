import logging
import os
from pathlib import Path

import pandas as pd
import tiktoken

from graphrag.query.context_builder.builders import LocalContextBuilder
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units, read_indexer_report_embeddings,
)
from graphrag.query.llm.base import BaseLLM, BaseTextEmbedding
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.drift_search.drift_context import DRIFTSearchContextBuilder
from graphrag.query.structured_search.drift_search.search import DRIFTSearch
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores import VectorStoreType, VectorStoreFactory, BaseVectorStore
from webserver.configs import settings
from webserver.utils import consts

logger = logging.getLogger(__name__)


async def load_local_context(input_dir: str, embedder: BaseTextEmbedding,
                             token_encoder: tiktoken.Encoding | None = None) -> LocalContextBuilder:
    # read nodes table to get community and degree data
    entity_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")

    entities = read_indexer_entities(entity_df, entity_embedding_df, consts.COMMUNITY_LEVEL)

    vector_store_type = settings.embeddings.vector_store.get("type", VectorStoreType.LanceDB)  # type: ignore
    vector_store_args = settings.embeddings.vector_store
    if vector_store_type == VectorStoreType.LanceDB:
        db_uri = settings.embeddings.vector_store["db_uri"]  # type: ignore
        lancedb_dir = Path(settings.data).parent.resolve() / db_uri
        vector_store_args["db_uri"] = str(lancedb_dir)  # type: ignore

    description_embedding_store = _get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        container_suffix="entity-description",
    )

    relationship_df = pd.read_parquet(f"{input_dir}/{consts.RELATIONSHIP_TABLE}.parquet")
    relationships = read_indexer_relationships(relationship_df)

    covariate_file = f"{input_dir}/{consts.COVARIATE_TABLE}.parquet"
    if os.path.exists(covariate_file):
        covariate_df = pd.read_parquet(covariate_file)
        claims = read_indexer_covariates(covariate_df)
        covariates = {"claims": claims}
    else:
        covariates = None

    report_df = pd.read_parquet(f"{input_dir}/{consts.COMMUNITY_REPORT_TABLE}.parquet")
    reports = read_indexer_reports(report_df, entity_df, consts.COMMUNITY_LEVEL)

    text_unit_df = pd.read_parquet(f"{input_dir}/{consts.TEXT_UNIT_TABLE}.parquet")
    text_units = read_indexer_text_units(text_unit_df)

    context_builder = LocalSearchMixedContext(
        community_reports=reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        covariates=covariates,
        entity_text_embeddings=description_embedding_store,
        embedding_vectorstore_key=EntityVectorStoreKey.ID,
        # if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
        text_embedder=embedder,
        token_encoder=token_encoder,
    )
    return context_builder


def _get_embedding_store(
        config_args: dict,
        container_suffix: str,
) -> BaseVectorStore:
    """Get the embedding description store."""
    vector_store_type = config_args["type"]
    collection_name = (
        f"{config_args.get('container_name', 'default')}-{container_suffix}"
    )
    embedding_store = VectorStoreFactory.get_vector_store(
        vector_store_type=vector_store_type,
        kwargs={**config_args, "collection_name": collection_name},
    )
    embedding_store.connect(**config_args)
    return embedding_store


async def build_local_question_gen(llm: BaseLLM, context_builder: LocalContextBuilder = None,
                                   token_encoder: tiktoken.Encoding | None = None) -> LocalQuestionGen:
    local_context_params = {
        "text_unit_prop": settings.local_search.text_unit_prop,
        "community_prop": settings.local_search.community_prop,
        "conversation_history_max_turns": settings.local_search.conversation_history_max_turns,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": settings.local_search.top_k_entities,
        "top_k_relationships": settings.local_search.top_k_relationships,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,
        # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": settings.local_search.max_tokens,
    }

    llm_params = {
        "max_tokens": settings.local_search.llm_max_tokens,
        "temperature": settings.local_search.temperature,
        "top_p": settings.local_search.top_p,
        "n": settings.local_search.n,
    }

    question_generator = LocalQuestionGen(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=llm_params,
        context_builder_params=local_context_params,
    )

    return question_generator


async def build_local_search_engine(llm: BaseLLM, context_builder: LocalContextBuilder = None,
                                    token_encoder: tiktoken.Encoding | None = None) -> LocalSearch:
    local_context_params = {
        "text_unit_prop": settings.local_search.text_unit_prop,
        "community_prop": settings.local_search.community_prop,
        "conversation_history_max_turns": settings.local_search.conversation_history_max_turns,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": settings.local_search.top_k_entities,
        "top_k_relationships": settings.local_search.top_k_relationships,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,
        # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": settings.local_search.max_tokens,
    }

    llm_params = {
        "max_tokens": settings.local_search.llm_max_tokens,
        "temperature": settings.local_search.temperature,
        "top_p": settings.local_search.top_p,
        "n": settings.local_search.n,
    }

    search_engine = LocalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=llm_params,
        context_builder_params=local_context_params,
        response_type="multiple paragraphs",
    )
    return search_engine


async def build_drift_search_context(llm: BaseLLM, input_dir: str,
                                     embedder: BaseTextEmbedding) -> DRIFTSearchContextBuilder:
    # read nodes table to get community and degree data
    entity_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")
    entities = read_indexer_entities(entity_df, entity_embedding_df, consts.COMMUNITY_LEVEL)

    relationship_df = pd.read_parquet(f"{input_dir}/{consts.RELATIONSHIP_TABLE}.parquet")
    relationships = read_indexer_relationships(relationship_df)

    report_df = pd.read_parquet(f"{input_dir}/{consts.COMMUNITY_REPORT_TABLE}.parquet")
    reports = read_indexer_reports(report_df, entity_df, consts.COMMUNITY_LEVEL)

    text_unit_df = pd.read_parquet(f"{input_dir}/{consts.TEXT_UNIT_TABLE}.parquet")
    text_units = read_indexer_text_units(text_unit_df)

    # vector store
    vector_store_type = settings.embeddings.vector_store.get("type", VectorStoreType.LanceDB)  # type: ignore
    vector_store_args = settings.embeddings.vector_store
    if vector_store_type == VectorStoreType.LanceDB:
        db_uri = settings.embeddings.vector_store["db_uri"]  # type: ignore
        lancedb_dir = Path(settings.data).parent.resolve() / db_uri
        vector_store_args["db_uri"] = str(lancedb_dir)  # type: ignore

    description_embedding_store = _get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        container_suffix="entity-description",
    )

    full_content_embedding_store = _get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        container_suffix="community-full_content",
    )
    read_indexer_report_embeddings(reports, full_content_embedding_store)

    return DRIFTSearchContextBuilder(
        chat_llm=llm,
        text_embedder=embedder,
        entities=entities,
        relationships=relationships,
        reports=reports,
        entity_text_embeddings=description_embedding_store,
        text_units=text_units,
    )


async def build_drift_search_engine(llm: BaseLLM, context_builder: DRIFTSearchContextBuilder = None,
                                    token_encoder: tiktoken.Encoding | None = None) -> DRIFTSearch:
    return DRIFTSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
    )
