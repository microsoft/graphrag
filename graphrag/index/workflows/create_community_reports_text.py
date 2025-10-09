# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
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
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.protocol.base import ChatModel
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.tokenizer.tokenizer import Tokenizer
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
    model = ModelManager().get_or_create_chat_model(
        name="community_reporting",
        model_type=model_config.type,
        config=model_config,
        callbacks=context.callbacks,
        cache=context.cache,
    )

    tokenizer = get_tokenizer(model_config)

    prompts = config.community_reports.resolved_prompts(config.root_dir)

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
        num_threads=model_config.concurrent_requests,
        async_type=model_config.async_mode,
    )

    await write_table_to_storage(output, "community_reports", context.output_storage)

    logger.info("Workflow completed: create_community_reports_text")
    return WorkflowFunctionOutput(result=output)


async def create_community_reports_text(
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: ChatModel,
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
