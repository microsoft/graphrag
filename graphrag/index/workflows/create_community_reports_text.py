# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.finalize_community_reports import (
    finalize_community_reports,
)
from graphrag.index.operations.summarize_communities.explode_communities import (
    explode_communities,
)
from graphrag.index.operations.summarize_communities.summarize_communities import (
    summarize_communities,
)
from graphrag.index.operations.summarize_communities.text_unit_context.context_builder import (
    build_level_context,
    build_local_context,
)
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

log = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    entities = await load_table_from_storage("entities", context.storage)
    communities = await load_table_from_storage("communities", context.storage)

    text_units = await load_table_from_storage("text_units", context.storage)

    community_reports_llm_settings = config.get_language_model_config(
        config.community_reports.model_id
    )
    async_mode = community_reports_llm_settings.async_mode
    num_threads = community_reports_llm_settings.concurrent_requests
    summarization_strategy = config.community_reports.resolved_strategy(
        config.root_dir, community_reports_llm_settings
    )

    output = await create_community_reports_text(
        entities,
        communities,
        text_units,
        context.callbacks,
        context.cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    await write_table_to_storage(output, "community_reports", context.storage)

    return WorkflowFunctionOutput(result=output)


async def create_community_reports_text(
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    nodes = explode_communities(communities, entities)

    summarization_strategy["extraction_prompt"] = summarization_strategy["text_prompt"]

    max_input_length = summarization_strategy.get(
        "max_input_length", graphrag_config_defaults.community_reports.max_input_length
    )

    local_contexts = build_local_context(
        communities, text_units, nodes, max_input_length
    )

    community_reports = await summarize_communities(
        nodes,
        communities,
        local_contexts,
        build_level_context,
        callbacks,
        cache,
        summarization_strategy,
        max_input_length=max_input_length,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return finalize_community_reports(community_reports, communities)
