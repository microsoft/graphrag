# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any
from uuid import uuid4

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.extract_entities import extract_entities
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
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    entities, relationships = await extract_entities(
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

    if not _validate_data(entities):
        error_msg = "Entity Extraction failed. No entities detected during extraction."
        callbacks.error(error_msg)
        raise ValueError(error_msg)

    if not _validate_data(relationships):
        error_msg = (
            "Entity Extraction failed. No relationships detected during extraction."
        )
        callbacks.error(error_msg)
        raise ValueError(error_msg)

    entity_summaries, relationship_summaries = await summarize_descriptions(
        entities_df=entities,
        relationships_df=relationships,
        callbacks=callbacks,
        cache=cache,
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )

    base_relationship_edges = _prep_edges(relationships, relationship_summaries)

    base_entity_nodes = _prep_nodes(entities, entity_summaries)

    return (base_entity_nodes, base_relationship_edges)


def _prep_nodes(entities, summaries) -> pd.DataFrame:
    entities.drop(columns=["description"], inplace=True)
    nodes = entities.merge(summaries, on="title", how="left").drop_duplicates(
        subset="title"
    )
    nodes = nodes.loc[nodes["title"].notna()].reset_index()
    nodes["human_readable_id"] = nodes.index
    nodes["id"] = nodes["human_readable_id"].apply(lambda _x: str(uuid4()))
    return nodes


def _prep_edges(relationships, summaries) -> pd.DataFrame:
    edges = (
        relationships.drop(columns=["description"])
        .drop_duplicates(subset=["source", "target"])
        .merge(summaries, on=["source", "target"], how="left")
    )
    edges["human_readable_id"] = edges.index
    edges["id"] = edges["human_readable_id"].apply(lambda _x: str(uuid4()))
    return edges


def _validate_data(df: pd.DataFrame) -> bool:
    """Validate that the dataframe has data."""
    return len(df) > 0
