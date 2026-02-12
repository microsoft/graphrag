# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from typing import TYPE_CHECKING

import pandas as pd
from graphrag_llm.completion import create_completion
from graphrag_llm.tokenizer import Tokenizer

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
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

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    logger.info("Workflow started: create_community_reports_text")
    reader = DataReader(context.output_table_provider)
    entities = await reader.entities()
    communities = await reader.communities()
    text_units = await reader.text_units()

    model_config = config.get_completion_model_config(
        config.community_reports.completion_model_id
    )
    model = create_completion(
        model_config,
        cache=context.cache.child(config.community_reports.model_instance_name),
        cache_key_creator=cache_key_creator,
    )

    tokenizer = model.tokenizer

    prompts = config.community_reports.resolved_prompts()

    output = await create_community_reports_text(
        entities,
        communities,
        text_units,
        context.callbacks,
        model=model,
        tokenizer=tokenizer,
        prompt=prompts.text_prompt,
        max_input_length=config.community_reports.max_input_length,
        max_report_length=config.community_reports.max_length,
        num_threads=config.concurrent_requests,
        async_type=config.async_mode,
    )

    await context.output_table_provider.write_dataframe("community_reports", output)

    logger.info("Workflow completed: create_community_reports_text")
    return WorkflowFunctionOutput(result=output)


async def create_community_reports_text(
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: "LLMCompletion",
    tokenizer: Tokenizer,
    prompt: str,
    max_input_length: int,
    max_report_length: int,
    num_threads: int,
    async_type: AsyncType,
) -> pd.DataFrame:
    """All the steps to transform community reports."""
    nodes = explode_communities(communities, entities)

    local_contexts = build_local_context(
        communities, text_units, nodes, tokenizer, max_input_length
    )

    community_reports = await summarize_communities(
        nodes,
        communities,
        local_contexts,
        build_level_context,
        callbacks,
        model=model,
        prompt=prompt,
        tokenizer=tokenizer,
        max_input_length=max_input_length,
        max_report_length=max_report_length,
        num_threads=num_threads,
        async_type=async_type,
    )

    return finalize_community_reports(community_reports, communities)
