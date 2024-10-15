# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

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
from graphrag.index.flows.create_base_entity_graph import (
    create_base_entity_graph as create_base_entity_graph_flow,
)
from graphrag.index.storage import PipelineStorage


@verb(
    name="create_base_entity_graph",
    treats_input_tables_as_immutable=True,
)
async def create_base_entity_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    text_column: str,
    id_column: str,
    clustering_strategy: dict[str, Any],
    extraction_strategy: dict[str, Any] | None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    node_merge_config: dict[str, Any] | None = None,
    edge_merge_config: dict[str, Any] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
    embedding_strategy: dict[str, Any] | None = None,
    graphml_snapshot_enabled: bool = False,
    raw_entity_snapshot_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_base_entity_graph_flow(
        source,
        callbacks,
        cache,
        storage,
        text_column,
        id_column,
        clustering_strategy=clustering_strategy,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extraction_num_threads,
        extraction_async_mode=extraction_async_mode,
        entity_types=entity_types,
        node_merge_config=node_merge_config,
        edge_merge_config=edge_merge_config,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
        embedding_strategy=embedding_strategy,
        graphml_snapshot_enabled=graphml_snapshot_enabled,
        raw_entity_snapshot_enabled=raw_entity_snapshot_enabled,
    )

    return create_verb_result(cast(Table, output))
