import pandas as pd
import tiktoken

from graphrag.query.context_builder.builders import GlobalContextBuilder
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_reports
from graphrag.query.llm.base import BaseLLM
from graphrag.query.structured_search.global_search.callbacks import GlobalSearchLLMCallback
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch

from webserver.configs import settings
from webserver.utils import consts


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


async def build_global_search_engine(llm: BaseLLM, context_builder=None, callback: GlobalSearchLLMCallback = None,
                                     token_encoder: tiktoken.Encoding | None = None, **kwargs) -> GlobalSearch:

    max_tokens = int(kwargs.get('max_tokens', settings.global_search.max_tokens))
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
        "max_tokens": max_tokens,
        "context_name": "Reports",
    }

    map_llm_params = {
        **kwargs,
        "response_format": {"type": "json_object"},
    }

    search_engine = GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        max_data_tokens=max_tokens,
        map_llm_params=map_llm_params,
        reduce_llm_params=kwargs,
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

