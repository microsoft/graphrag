# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.entities.extraction.entity_extract import entity_extract_df
from graphrag.index.verbs.graph.merge.merge_graphs import merge_graphs_df
from graphrag.index.verbs.snapshot import snapshot_df
from graphrag.index.verbs.snapshot_rows import snapshot_rows_df


@verb(name="create_base_extracted_entities", treats_input_tables_as_immutable=True)
async def create_base_extracted_entities(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    column: str,
    id_column: str,
    nodes: dict[str, Any],
    edges: dict[str, Any],
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    graphml_snapshot_enabled: bool = False,
    raw_entity_snapshot_enabled: bool = False,
    **kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format covariates."""
    source = cast(pd.DataFrame, input.get_input())

    entity_graph = await entity_extract_df(
        source,
        cache,
        callbacks,
        column=column,
        id_column=id_column,
        strategy=strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        to="entities",
        graph_to="entity_graph",
        **kwargs,
    )

    if raw_entity_snapshot_enabled:
        await snapshot_df(
            entity_graph,
            name="raw_extracted_entities",
            storage=storage,
            formats=["json"],
        )

    merged_graph = merge_graphs_df(
        entity_graph,
        callbacks,
        column="entity_graph",
        to="entity_graph",
        nodes=nodes,
        edges=edges,
    )

    if graphml_snapshot_enabled:
        await snapshot_rows_df(
            merged_graph,
            base_name="merged_graph",
            column="entity_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    return create_verb_result(cast(Table, merged_graph))
