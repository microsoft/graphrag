# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.entities import _group_and_resolve_entities
from graphrag.index.update.relationships import _update_and_merge_relationships
from graphrag.index.workflows.extract_graph import get_summarized_entities_relationships
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the entities and relationships from a incremental index run."""
    logger.info("Updating Entities and Relationships")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )

    (
        merged_entities_df,
        merged_relationships_df,
        entity_id_mapping,
    ) = await _update_entities_and_relationships(
        previous_storage,
        delta_storage,
        output_storage,
        config,
        context.cache,
        context.callbacks,
    )

    context.state["incremental_update_merged_entities"] = merged_entities_df
    context.state["incremental_update_merged_relationships"] = merged_relationships_df
    context.state["incremental_update_entity_id_mapping"] = entity_id_mapping

    return WorkflowFunctionOutput(result=None)


async def _update_entities_and_relationships(
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
    config: GraphRagConfig,
    cache: PipelineCache,
    callbacks: WorkflowCallbacks,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Update Final Entities  and Relationships output."""
    old_entities = await load_table_from_storage("entities", previous_storage)
    delta_entities = await load_table_from_storage("entities", delta_storage)

    merged_entities_df, entity_id_mapping = _group_and_resolve_entities(
        old_entities, delta_entities
    )

    # Update Relationships
    old_relationships = await load_table_from_storage("relationships", previous_storage)
    delta_relationships = await load_table_from_storage("relationships", delta_storage)
    merged_relationships_df = _update_and_merge_relationships(
        old_relationships,
        delta_relationships,
    )

    summarization_llm_settings = config.get_language_model_config(
        config.summarize_descriptions.model_id
    )
    summarization_strategy = config.summarize_descriptions.resolved_strategy(
        config.root_dir, summarization_llm_settings
    )

    (
        merged_entities_df,
        merged_relationships_df,
    ) = await get_summarized_entities_relationships(
        extracted_entities=merged_entities_df,
        extracted_relationships=merged_relationships_df,
        callbacks=callbacks,
        cache=cache,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_llm_settings.concurrent_requests,
    )

    # Save the updated entities back to storage
    await write_table_to_storage(merged_entities_df, "entities", output_storage)

    await write_table_to_storage(
        merged_relationships_df, "relationships", output_storage
    )

    return merged_entities_df, merged_relationships_df, entity_id_mapping
