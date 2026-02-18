# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the resolve_entities workflow definition."""

import logging
from typing import TYPE_CHECKING

from graphrag_llm.completion import create_completion

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.operations.resolve_entities.resolve_entities import (
    resolve_entities,
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
    """Resolve duplicate entities with different surface forms."""
    logger.info("Workflow started: resolve_entities")

    if not config.entity_resolution.enabled:
        logger.info(
            "Entity resolution is disabled (entity_resolution.enabled=false), skipping"
        )
        return WorkflowFunctionOutput(result={})

    reader = DataReader(context.output_table_provider)
    entities = await reader.entities()
    relationships = await reader.relationships()

    resolution_model_config = config.get_completion_model_config(
        config.entity_resolution.completion_model_id
    )
    resolution_prompts = config.entity_resolution.resolved_prompts()
    resolution_model = create_completion(
        resolution_model_config,
        cache=context.cache.child(config.entity_resolution.model_instance_name),
        cache_key_creator=cache_key_creator,
    )

    resolved_entities, resolved_relationships = await resolve_entities(
        entities=entities,
        relationships=relationships,
        callbacks=context.callbacks,
        model=resolution_model,
        prompt=resolution_prompts.resolution_prompt,
        batch_size=config.entity_resolution.batch_size,
        num_threads=config.concurrent_requests,
    )

    await context.output_table_provider.write_dataframe("entities", resolved_entities)
    await context.output_table_provider.write_dataframe(
        "relationships", resolved_relationships
    )

    logger.info("Workflow completed: resolve_entities")
    return WorkflowFunctionOutput(
        result={
            "entities": resolved_entities,
            "relationships": resolved_relationships,
        }
    )
