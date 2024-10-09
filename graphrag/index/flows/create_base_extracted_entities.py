# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

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
from graphrag.index.storage import PipelineStorage


async def create_base_extracted_entities(
    text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    column: str,
    id_column: str,
    nodes: dict[str, Any],
    edges: dict[str, Any],
    extraction_strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    graphml_snapshot_enabled: bool = False,
    raw_entity_snapshot_enabled: bool = False,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to extract and format covariates."""
    entity_graph = await extract_entities(
        text_units,
        callbacks,
        cache,
        column=column,
        id_column=id_column,
        strategy=extraction_strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        to="entities",
        graph_to="entity_graph",
        num_threads=num_threads,
    )

    if raw_entity_snapshot_enabled:
        await snapshot(
            entity_graph,
            name="raw_extracted_entities",
            storage=storage,
            formats=["json"],
        )

    merged_graph = merge_graphs(
        entity_graph,
        callbacks,
        column="entity_graph",
        to="entity_graph",
        nodes=nodes,
        edges=edges,
    )

    if graphml_snapshot_enabled:
        await snapshot_rows(
            merged_graph,
            base_name="merged_graph",
            column="entity_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    return merged_graph
