# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.index.operations.extract_graph.extract_graph import (
    extract_graph as extractor,
)
from graphrag.index.operations.finalize_entities import finalize_entities
from graphrag.index.operations.finalize_relationships import finalize_relationships
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    extraction_strategy: dict[str, Any] | None = None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    embed_config: EmbedGraphConfig | None = None,
    layout_enabled: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    extracted_entities, extracted_relationships = await extractor(
        text_units=text_units,
        callbacks=callbacks,
        cache=cache,
        text_column="text",
        id_column="id",
        strategy=extraction_strategy,
        async_mode=extraction_async_mode,
        entity_types=entity_types,
        num_threads=extraction_num_threads,
    )

    if not _validate_data(extracted_entities):
        error_msg = "Entity Extraction failed. No entities detected during extraction."
        callbacks.error(error_msg)
        raise ValueError(error_msg)

    if not _validate_data(extracted_relationships):
        error_msg = (
            "Entity Extraction failed. No relationships detected during extraction."
        )
        callbacks.error(error_msg)
        raise ValueError(error_msg)

    entity_summaries, relationship_summaries = await summarize_descriptions(
        entities_df=extracted_entities,
        relationships_df=extracted_relationships,
        callbacks=callbacks,
        cache=cache,
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )

    relationships = extracted_relationships.drop(columns=["description"]).merge(
        relationship_summaries, on=["source", "target"], how="left"
    )

    extracted_entities.drop(columns=["description"], inplace=True)
    entities = extracted_entities.merge(entity_summaries, on="title", how="left")

    final_entities = finalize_entities(
        entities, relationships, callbacks, embed_config, layout_enabled
    )
    final_relationships = finalize_relationships(relationships)
    return (final_entities, final_relationships)


def _validate_data(df: pd.DataFrame) -> bool:
    """Validate that the dataframe has data."""
    return len(df) > 0
