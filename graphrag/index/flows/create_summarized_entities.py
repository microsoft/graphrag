# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to summarize entities."""

from typing import Any

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.extract_entities import extract_entities
from graphrag.index.operations.merge_graphs import merge_graphs
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.snapshot_rows import snapshot_rows
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)
from graphrag.index.storage import PipelineStorage


async def create_summarized_entities(
    text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    column: str,
    id_column: str,
    extraction_strategy: dict[str, Any] | None = None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    node_merge_config: dict[str, Any] | None = None,
    edge_merge_config: dict[str, Any] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    graphml_snapshot_enabled: bool = False,
    raw_entity_snapshot_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to extract and summarize entities."""
    entity_graph = await extract_entities(
        text_units,
        callbacks,
        cache,
        column=column,
        id_column=id_column,
        strategy=extraction_strategy,
        async_mode=extraction_async_mode,
        entity_types=entity_types,
        to="entities",
        graph_to="entity_graph",
        num_threads=extraction_num_threads,
    )

    merged_graph = merge_graphs(
        entity_graph,
        callbacks,
        column="entity_graph",
        to="entity_graph",
        node_operations=node_merge_config,
        edge_operations=edge_merge_config,
    )

    summarized = await summarize_descriptions(
        merged_graph,
        callbacks,
        cache,
        column="entity_graph",
        to="entity_graph",
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )

    if raw_entity_snapshot_enabled:
        await snapshot(
            entity_graph,
            name="raw_extracted_entities",
            storage=storage,
            formats=["json"],
        )

    if graphml_snapshot_enabled:
        await snapshot_rows(
            merged_graph,
            base_name="merged_graph",
            column="entity_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )
        await snapshot_rows(
            summarized,
            column="entity_graph",
            base_name="summarized_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    return summarized
