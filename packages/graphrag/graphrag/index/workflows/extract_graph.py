# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from typing import TYPE_CHECKING

import pandas as pd
from graphrag_llm.completion import create_completion

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.operations.extract_graph.extract_graph import (
    extract_graph as extractor,
)
from graphrag.index.operations.summarize_descriptions.summarize_descriptions import (
    summarize_descriptions,
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
    """All the steps to create the base entity graph."""
    logger.info("Workflow started: extract_graph")
    reader = DataReader(context.output_table_provider)
    text_units = await reader.text_units()

    extraction_model_config = config.get_completion_model_config(
        config.extract_graph.completion_model_id
    )
    extraction_prompts = config.extract_graph.resolved_prompts()
    extraction_model = create_completion(
        extraction_model_config,
        cache=context.cache.child(config.extract_graph.model_instance_name),
        cache_key_creator=cache_key_creator,
    )

    summarization_model_config = config.get_completion_model_config(
        config.summarize_descriptions.completion_model_id
    )
    summarization_prompts = config.summarize_descriptions.resolved_prompts()
    summarization_model = create_completion(
        summarization_model_config,
        cache=context.cache.child(config.summarize_descriptions.model_instance_name),
        cache_key_creator=cache_key_creator,
    )

    entities, relationships, raw_entities, raw_relationships = await extract_graph(
        text_units=text_units,
        callbacks=context.callbacks,
        extraction_model=extraction_model,
        extraction_prompt=extraction_prompts.extraction_prompt,
        entity_types=config.extract_graph.entity_types,
        max_gleanings=config.extract_graph.max_gleanings,
        extraction_num_threads=config.concurrent_requests,
        extraction_async_type=config.async_mode,
        summarization_model=summarization_model,
        max_summary_length=config.summarize_descriptions.max_length,
        max_input_tokens=config.summarize_descriptions.max_input_tokens,
        summarization_prompt=summarization_prompts.summarize_prompt,
        summarization_num_threads=config.concurrent_requests,
    )

    await context.output_table_provider.write_dataframe("entities", entities)
    await context.output_table_provider.write_dataframe("relationships", relationships)

    if config.snapshots.raw_graph:
        await context.output_table_provider.write_dataframe(
            "raw_entities", raw_entities
        )
        await context.output_table_provider.write_dataframe(
            "raw_relationships", raw_relationships
        )

    logger.info("Workflow completed: extract_graph")
    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    extraction_model: "LLMCompletion",
    extraction_prompt: str,
    entity_types: list[str],
    max_gleanings: int,
    extraction_num_threads: int,
    extraction_async_type: AsyncType,
    summarization_model: "LLMCompletion",
    max_summary_length: int,
    max_input_tokens: int,
    summarization_prompt: str,
    summarization_num_threads: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    extracted_entities, extracted_relationships = await extractor(
        text_units=text_units,
        callbacks=callbacks,
        text_column="text",
        id_column="id",
        model=extraction_model,
        prompt=extraction_prompt,
        entity_types=entity_types,
        max_gleanings=max_gleanings,
        num_threads=extraction_num_threads,
        async_type=extraction_async_type,
    )

    if len(extracted_entities) == 0:
        error_msg = "Graph Extraction failed. No entities detected during extraction."
        logger.error(error_msg)
        raise ValueError(error_msg)

    if len(extracted_relationships) == 0:
        error_msg = (
            "Graph Extraction failed. No relationships detected during extraction."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # copy these as is before any summarization
    raw_entities = extracted_entities.copy()
    raw_relationships = extracted_relationships.copy()

    entities, relationships = await get_summarized_entities_relationships(
        extracted_entities=extracted_entities,
        extracted_relationships=extracted_relationships,
        callbacks=callbacks,
        model=summarization_model,
        max_summary_length=max_summary_length,
        max_input_tokens=max_input_tokens,
        summarization_prompt=summarization_prompt,
        num_threads=summarization_num_threads,
    )

    return (entities, relationships, raw_entities, raw_relationships)


async def get_summarized_entities_relationships(
    extracted_entities: pd.DataFrame,
    extracted_relationships: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: "LLMCompletion",
    max_summary_length: int,
    max_input_tokens: int,
    summarization_prompt: str,
    num_threads: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize the entities and relationships."""
    entity_summaries, relationship_summaries = await summarize_descriptions(
        entities_df=extracted_entities,
        relationships_df=extracted_relationships,
        callbacks=callbacks,
        model=model,
        max_summary_length=max_summary_length,
        max_input_tokens=max_input_tokens,
        prompt=summarization_prompt,
        num_threads=num_threads,
    )

    relationships = extracted_relationships.drop(columns=["description"]).merge(
        relationship_summaries, on=["source", "target"], how="left"
    )

    extracted_entities.drop(columns=["description"], inplace=True)
    entities = extracted_entities.merge(entity_summaries, on="title", how="left")
    return entities, relationships
