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


async def load_global_context(input_dir: str,
                              token_encoder: tiktoken.Encoding | None = None) -> GlobalContextBuilder:
    final_nodes = pd.read_parquet(f"{input_dir}/{consts.ENTITY_TABLE}.parquet")
    final_community_reports = pd.read_parquet(f"{input_dir}/{consts.COMMUNITY_REPORT_TABLE}.parquet")
    final_entities = pd.read_parquet(f"{input_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")

    reports = read_indexer_reports(final_community_reports, final_nodes, consts.COMMUNITY_LEVEL)
    entities = read_indexer_entities(final_nodes, final_entities, consts.COMMUNITY_LEVEL)

    context_builder = GlobalCommunityContext(
        community_reports=reports,
        entities=entities,  # default to None if you don't want to use community weights for ranking
        token_encoder=token_encoder,
    )
    return context_builder


async def build_global_search_engine(llm: BaseLLM, context_builder=None, callback: GlobalSearchLLMCallback = None,
                                     token_encoder: tiktoken.Encoding | None = None) -> GlobalSearch:
    context_builder_params = {
        "use_community_summary": False,
        "shuffle_data": True,
        "include_community_rank": True,
        "min_community_rank": 0,
        "community_rank_name": "rank",
        "include_community_weight": True,
        "community_weight_name": "occurrence weight",
        "normalize_community_weight": True,
        "max_tokens": settings.global_search.max_tokens,
        "context_name": "Reports",
    }

    map_llm_params = {
        "max_tokens": settings.global_search.map_max_tokens,
        "temperature": settings.global_search.temperature,
        "top_p": settings.global_search.top_p,
        "n": settings.global_search.n,
        "response_format": {"type": "json_object"},
    }

    reduce_llm_params = {
        "max_tokens": settings.global_search.reduce_max_tokens,
        "temperature": settings.global_search.temperature,
        "top_p": settings.global_search.top_p,
        "n": settings.global_search.n,
    }

    search_engine = GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        max_data_tokens=settings.global_search.data_max_tokens,
        map_llm_params=map_llm_params,
        reduce_llm_params=reduce_llm_params,
        allow_general_knowledge=False,
        json_mode=settings.llm.model_supports_json,  # set this to False if your LLM model does not support JSON mode.
        context_builder_params=context_builder_params,
        concurrent_coroutines=settings.global_search.concurrency,
        callbacks=[callback] if callback else None,
        # free form text describing the response type and format, can be anything,
        # e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
        response_type="multiple paragraphs",
    )
    return search_engine
