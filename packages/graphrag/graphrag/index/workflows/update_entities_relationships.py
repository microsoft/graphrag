# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd
from graphrag_cache import Cache
from graphrag_llm.completion import create_completion
from graphrag_storage.tables.table_provider import TableProvider

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.run.utils import get_update_table_providers
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.entities import _group_and_resolve_entities
from graphrag.index.update.relationships import _update_and_merge_relationships
from graphrag.index.workflows.extract_graph import get_summarized_entities_relationships

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the entities and relationships from a incremental index run."""
    logger.info("Workflow started: update_entities_relationships")
    output_table_provider, previous_table_provider, delta_table_provider = (
        get_update_table_providers(config, context.state["update_timestamp"])
    )

    (
        merged_entities_df,
        merged_relationships_df,
        entity_id_mapping,
    ) = await _update_entities_and_relationships(
        previous_table_provider,
        delta_table_provider,
        output_table_provider,
        config,
        context.cache,
        context.callbacks,
    )

    context.state["incremental_update_merged_entities"] = merged_entities_df
    context.state["incremental_update_merged_relationships"] = merged_relationships_df
    context.state["incremental_update_entity_id_mapping"] = entity_id_mapping

    logger.info("Workflow completed: update_entities_relationships")
    return WorkflowFunctionOutput(result=None)


async def _update_entities_and_relationships(
    previous_table_provider: TableProvider,
    delta_table_provider: TableProvider,
    output_table_provider: TableProvider,
    config: GraphRagConfig,
    cache: Cache,
    callbacks: WorkflowCallbacks,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Update Final Entities  and Relationships output."""
    old_entities = await DataReader(previous_table_provider).entities()
    delta_entities = await DataReader(delta_table_provider).entities()

    merged_entities_df, entity_id_mapping = _group_and_resolve_entities(
        old_entities, delta_entities
    )

    # Update Relationships
    old_relationships = await DataReader(previous_table_provider).relationships()
    delta_relationships = await DataReader(delta_table_provider).relationships()
    merged_relationships_df = _update_and_merge_relationships(
        old_relationships,
        delta_relationships,
    )

    summarization_model_config = config.get_completion_model_config(
        config.summarize_descriptions.completion_model_id
    )
    prompts = config.summarize_descriptions.resolved_prompts()
    model = create_completion(
        summarization_model_config,
        cache=cache.child("summarize_descriptions"),
        cache_key_creator=cache_key_creator,
    )

    (
        merged_entities_df,
        merged_relationships_df,
    ) = await get_summarized_entities_relationships(
        extracted_entities=merged_entities_df,
        extracted_relationships=merged_relationships_df,
        callbacks=callbacks,
        model=model,
        max_summary_length=config.summarize_descriptions.max_length,
        max_input_tokens=config.summarize_descriptions.max_input_tokens,
        summarization_prompt=prompts.summarize_prompt,
        num_threads=config.concurrent_requests,
    )

    # Save the updated entities back to storage
    await output_table_provider.write_dataframe("entities", merged_entities_df)
    await output_table_provider.write_dataframe(
        "relationships", merged_relationships_df
    )

    return merged_entities_df, merged_relationships_df, entity_id_mapping
