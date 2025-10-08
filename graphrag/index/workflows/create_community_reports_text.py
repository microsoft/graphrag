# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
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
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    logger.info("Workflow started: create_community_reports_text")
    entities = await load_table_from_storage("entities", context.output_storage)
    communities = await load_table_from_storage("communities", context.output_storage)

    text_units = await load_table_from_storage("text_units", context.output_storage)

    model_config = config.get_language_model_config(config.community_reports.model_id)
    prompts = config.community_reports.resolved_prompts(config.root_dir)

    output = await create_community_reports_text(
        entities,
        communities,
        text_units,
        context.callbacks,
        context.cache,
        model_config=model_config,
        prompt=prompts["text_prompt"],
        max_input_length=config.community_reports.max_input_length,
        max_report_length=config.community_reports.max_length,
    )

    await write_table_to_storage(output, "community_reports", context.output_storage)

    logger.info("Workflow completed: create_community_reports_text")
    return WorkflowFunctionOutput(result=output)


async def create_community_reports_text(
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    prompt: str,
    max_input_length: int = 8000,
    max_report_length: int = 1500,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    nodes = explode_communities(communities, entities)

    tokenizer = get_tokenizer(model_config)

    local_contexts = build_local_context(
        communities, text_units, nodes, tokenizer, max_input_length
    )

    community_reports = await summarize_communities(
        nodes,
        communities,
        local_contexts,
        build_level_context,
        callbacks,
        cache,
        model_config=model_config,
        prompt=prompt,
        tokenizer=tokenizer,
        max_input_length=max_input_length,
        max_report_length=max_report_length,
    )

    return finalize_community_reports(community_reports, communities)
