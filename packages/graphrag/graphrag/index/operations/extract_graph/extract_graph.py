# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing extract_graph method."""

import logging
from typing import TYPE_CHECKING

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.extract_graph.graph_extractor import GraphExtractor
from graphrag.index.utils.derive_from_rows import derive_from_rows

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    text_column: str,
    id_column: str,
    model: "LLMCompletion",
    prompt: str,
    entity_types: list[str],
    max_gleanings: int,
    num_threads: int,
    async_type: AsyncType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract a graph from a piece of text using a language model."""
    num_started = 0

    async def run_strategy(row):
        nonlocal num_started
        text = row[text_column]
        id = row[id_column]
        result = await _run_extract_graph(
            text=text,
            source_id=id,
            entity_types=entity_types,
            model=model,
            prompt=prompt,
            max_gleanings=max_gleanings,
        )
        num_started += 1
        return result

    results = await derive_from_rows(
        text_units,
        run_strategy,
        callbacks,
        num_threads=num_threads,
        async_type=async_type,
        progress_msg="extract graph progress: ",
    )

    entity_dfs = []
    relationship_dfs = []
    for result in results:
        if result:
            entity_dfs.append(result[0])
            relationship_dfs.append(result[1])

    entities = _merge_entities(entity_dfs)
    relationships = _merge_relationships(relationship_dfs)

    return (entities, relationships)


async def _run_extract_graph(
    text: str,
    source_id: str,
    entity_types: list[str],
    model: "LLMCompletion",
    prompt: str,
    max_gleanings: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the graph intelligence entity extraction strategy."""
    extractor = GraphExtractor(
        model=model,
        prompt=prompt,
        max_gleanings=max_gleanings,
        on_error=lambda e, s, d: logger.error(
            "Entity Extraction Error", exc_info=e, extra={"stack": s, "details": d}
        ),
    )
    text = text.strip()

    entities_df, relationships_df = await extractor(
        text,
        entity_types=entity_types,
        source_id=source_id,
    )

    return (entities_df, relationships_df)


def _merge_entities(entity_dfs) -> pd.DataFrame:
    all_entities = pd.concat(entity_dfs, ignore_index=True)
    return (
        all_entities
        .groupby(["title", "type"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            frequency=("source_id", "count"),
        )
        .reset_index()
    )


def _merge_relationships(relationship_dfs) -> pd.DataFrame:
    all_relationships = pd.concat(relationship_dfs, ignore_index=False)
    return (
        all_relationships
        .groupby(["source", "target"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            weight=("weight", "sum"),
        )
        .reset_index()
    )
