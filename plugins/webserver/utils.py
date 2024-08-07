import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict

import pandas as pd
import tiktoken

from graphrag.query.cli import _infer_data_dir
from graphrag.query.context_builder.builders import LocalContextBuilder, GlobalContextBuilder
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import read_indexer_reports, read_indexer_entities, read_indexer_relationships, read_indexer_covariates, \
    read_indexer_text_units
from graphrag.query.input.loaders.dfs import store_entity_semantic_embeddings
from graphrag.query.llm.base import BaseLLM, BaseTextEmbedding
from graphrag.query.llm.oai import ChatOpenAI, OpenAIEmbedding, OpenaiApiType
from graphrag.query.structured_search.global_search.callbacks import GlobalSearchLLMCallback
from graphrag.query.structured_search.global_search.community_context import GlobalCommunityContext
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores import LanceDBVectorStore
from plugins.webserver import consts
from plugins.webserver.models import GraphRAGItem
from plugins.webserver.settings import settings


async def init_env():
    llm = ChatOpenAI(
        api_key=settings.api_key,
        api_base=settings.api_base,
        model=settings.llm_model,
        api_type=OpenaiApiType.OpenAI,
        max_retries=settings.max_retries,
    )

    text_embedder = OpenAIEmbedding(
        api_key=settings.api_key,
        api_base=settings.embedding_api_base,
        api_type=OpenaiApiType.OpenAI,
        model=settings.embedding_model,
        max_retries=settings.max_retries,
    )

    token_encoder = tiktoken.get_encoding("cl100k_base")

    local_search: LocalSearch = await build_local_search_engine(llm, token_encoder=token_encoder)
    global_search: GlobalSearch = await build_global_search_engine(llm, token_encoder=token_encoder)

    all_context = await load_all_context(settings.data, text_embedder, token_encoder)

    return llm, text_embedder, local_search, global_search, token_encoder, all_context


async def build_local_search_engine(llm: BaseLLM,
                                    context_builder: LocalContextBuilder = None,
                                    token_encoder: tiktoken.Encoding | None = None) -> LocalSearch:
    local_context_params = {
        "text_unit_prop": 0.5,
        "community_prop": 0.1,
        "conversation_history_max_turns": 5,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": 10,
        "top_k_relationships": 10,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,
        # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": settings.context_max_tokens,
    }
    llm_params = {
        "max_tokens": settings.response_max_tokens,
        "temperature": settings.temperature,
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


async def build_global_search_engine(llm: BaseLLM,
                                     context_builder=None,
                                     callback: GlobalSearchLLMCallback = None,
                                     token_encoder: tiktoken.Encoding | None = None) -> GlobalSearch:
    context_builder_params = {
        "use_community_summary": False,
        # False means using full community reports. True means using community short summaries.
        "shuffle_data": True,
        "include_community_rank": True,
        "min_community_rank": 0,
        "community_rank_name": "rank",
        "include_community_weight": True,
        "community_weight_name": "occurrence weight",
        "normalize_community_weight": True,
        "max_tokens": settings.context_max_tokens,
        "context_name": "Reports",
    }

    map_llm_params = {
        "max_tokens": settings.response_max_tokens,
        "temperature": settings.temperature,
        "response_format": {"type": "json_object"},
    }

    reduce_llm_params = {
        "max_tokens": settings.response_max_tokens,
        "temperature": settings.temperature,
    }

    search_engine = GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        max_data_tokens=settings.context_max_tokens,
        map_llm_params=map_llm_params,
        reduce_llm_params=reduce_llm_params,
        allow_general_knowledge=False,
        json_mode=True,  # set this to False if your LLM model does not support JSON mode.
        context_builder_params=context_builder_params,
        concurrent_coroutines=32,
        callbacks=[callback],
        # free form text describing the response type and format, can be anything,
        # e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
        response_type="multiple paragraphs",
    )
    return search_engine


async def build_global_context_builder(input_dir: str,
                                       token_encoder: tiktoken.Encoding | None = None) -> GlobalContextBuilder:
    entity_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    report_df = pd.read_parquet(f"{input_dir}/{consts.COMMUNITY_REPORT_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")

    reports = read_indexer_reports(report_df, entity_df, consts.COMMUNITY_LEVEL)
    entities = read_indexer_entities(entity_df, entity_embedding_df, consts.COMMUNITY_LEVEL)

    context_builder = GlobalCommunityContext(
        community_reports=reports,
        entities=entities,  # default to None if you don't want to use community weights for ranking
        token_encoder=token_encoder,
    )
    return context_builder


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

    documents_path = Path(f"{input_dir}/{consts.DOCUMENT_TABLE}.parquet")
    if documents_path.exists():
        documents_df = pd.read_parquet(documents_path)
    else:
        documents_df = None

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
        document=documents_df,
    )
    return context_builder


async def load_all_context(context_root_dir: str, text_embedder: OpenAIEmbedding, token_encoder: tiktoken.Encoding | None = None):
    all_context = {}
    root_dir = Path(context_root_dir)
    if root_dir.exists():
        for domain_dir in root_dir.iterdir():
            domain = domain_dir.name
            data_dir = _infer_data_dir(domain_dir)
            all_context[domain] = {} if domain not in all_context else all_context[domain]
            all_context[domain]['local'] = await load_local_context(data_dir, text_embedder, token_encoder)
            all_context[domain]['global'] = await build_global_context_builder(data_dir, token_encoder)
    return all_context


async def switch_context(domain: str, method: str, all_context: Dict) -> LocalContextBuilder:
    # switch index dir based on domain

    if method == "global":
        # context_builder = await build_global_context_builder(data_dir, token_encoder)
        context_builder = all_context[domain]['global']
    else:  # local
        # context_builder = await load_local_context(data_dir, text_embedder, token_encoder)
        context_builder = all_context[domain]['local']

    return context_builder


def delete_reference(text: str) -> str:
    pattern = re.compile(r'\[Data: ((?:Entities|Relationships|Sources|Claims|Reports) \((?:[\d, ]*[^,])(?:, \+more)?\)('r'?:; )?)+\]')
    return pattern.sub("", text)

    # data_dict = defaultdict(set)
    # for match in pattern.finditer(text):
    #     data_blocks = match.group(0)
    #     inner_pattern = re.compile(r'(Entities|Relationships|Sources|Claims|Reports) \(([\d, ,]*)(?:, \+more)?\)')
    #     for inner_match in inner_pattern.finditer(data_blocks):
    #         category = inner_match.group(1)
    #         numbers = inner_match.group(2).replace(" ", "").split(',')
    #         data_dict[category].update(map(int, filter(None, numbers)))  # filter to remove empty strings

    # return dict(data_dict)
