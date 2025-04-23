# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing entity_extract methods."""

import logging
from typing import Any

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.extract_graph.typing import (
    Document,
    EntityExtractStrategy,
    ExtractEntityStrategyType,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows

log = logging.getLogger(__name__)


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    text_column: str,
    id_column: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types=DEFAULT_ENTITY_TYPES,
    num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract a graph from a piece of text using a language model."""
    log.debug("entity_extract strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES
    strategy = strategy or {}
    strategy_exec = _load_strategy(
        strategy.get("type", ExtractEntityStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    # if max_retries is not set, inject a dynamically assigned value based on the total number of expected LLM calls to be made
    if strategy_config.get("llm") and strategy_config["llm"]["max_retries"] == -1:
        strategy_config["llm"]["max_retries"] = len(text_units)

    num_started = 0

    async def run_strategy(row):
        nonlocal num_started
        text = row[text_column]
        id = row[id_column]
        result = await strategy_exec(
            [Document(text=text, id=id)],
            entity_types,
            callbacks,
            cache,
            strategy_config,
        )
        num_started += 1
        return [result.entities, result.relationships, result.graph]

    results = await derive_from_rows(
        text_units,
        run_strategy,
        callbacks,
        async_type=async_mode,
        num_threads=num_threads,
    )

    entity_dfs = []
    relationship_dfs = []
    for result in results:
        if result:
            entity_dfs.append(pd.DataFrame(result[0]))
            relationship_dfs.append(pd.DataFrame(result[1]))

    entities = _merge_entities(entity_dfs)
    relationships = _merge_relationships(relationship_dfs)

    return (entities, relationships)


def _load_strategy(strategy_type: ExtractEntityStrategyType) -> EntityExtractStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case ExtractEntityStrategyType.graph_intelligence:
            from graphrag.index.operations.extract_graph.graph_intelligence_strategy import (
                run_graph_intelligence,
            )

            return run_graph_intelligence

        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)


def _merge_entities(entity_dfs) -> pd.DataFrame:
    all_entities = pd.concat(entity_dfs, ignore_index=True)
    return (
        all_entities.groupby(["title", "type"], sort=False)
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
        all_relationships.groupby(["source", "target"], sort=False)
        .agg(
            description=("description", list),
            text_unit_ids=("source_id", list),
            weight=("weight", "sum"),
        )
        .reset_index()
    )
