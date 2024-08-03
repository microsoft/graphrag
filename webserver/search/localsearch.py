import os
from typing import Any

import pandas as pd
import tiktoken
from graphrag.query.context_builder.builders import LocalContextBuilder
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.input.loaders.dfs import (
    store_entity_semantic_embeddings,
)
from graphrag.query.llm.base import BaseLLM, BaseTextEmbedding
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.lancedb import LanceDBVectorStore

from webserver.utils import consts
from webserver.configs import settings


async def load_local_context(input_dir: str, embedder: BaseTextEmbedding,
                             token_encoder: tiktoken.Encoding | None = None) -> LocalContextBuilder:
    # read nodes table to get community and degree data
    entity_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")

    entities = read_indexer_entities(entity_df, entity_embedding_df, consts.COMMUNITY_LEVEL)

    # load description embeddings to an in-memory lancedb vectorstore
    # to connect to a remote db, specify url and port values.
    description_embedding_store = LanceDBVectorStore(
        collection_name="entity_description_embeddings",
    )
    description_embedding_store.connect(db_uri=settings.lancedb_uri)
    entity_description_embeddings = store_entity_semantic_embeddings(
        entities=entities, vectorstore=description_embedding_store
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


async def build_local_question_gen(llm: BaseLLM, llm_params: dict[str, Any] | None = None, context_builder: LocalContextBuilder = None,
                                   token_encoder: tiktoken.Encoding | None = None, **kwargs) -> LocalQuestionGen:
    max_tokens = int(kwargs.get('max_tokens', settings.llm.max_tokens))

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
        "max_tokens": max_tokens,
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
                                    token_encoder: tiktoken.Encoding | None = None, **kwargs) -> LocalSearch:

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
        "max_tokens": int(kwargs.get('max_tokens', settings.llm.max_tokens)),
    }

    search_engine = LocalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=kwargs,
        context_builder_params=local_context_params,
        response_type="multiple paragraphs",
    )
    return search_engine

