# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.flows.create_base_entity_graph import (
    create_base_entity_graph as create_base_entity_graph_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage


@verb(
    name="create_base_entity_graph",
    treats_input_tables_as_immutable=True,
)
async def create_base_entity_graph(
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    runtime_storage: PipelineStorage,
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
    snapshot_graphml_enabled: bool = False,
    snapshot_raw_entities_enabled: bool = False,
    snapshot_transient_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to create the base entity graph."""
    text_units = await runtime_storage.get("base_text_units")

    output = await create_base_entity_graph_flow(
        text_units,
        callbacks,
        cache,
        storage,
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
        snapshot_graphml_enabled=snapshot_graphml_enabled,
        snapshot_raw_entities_enabled=snapshot_raw_entities_enabled,
        snapshot_transient_enabled=snapshot_transient_enabled,
    )

    await runtime_storage.set("base_entity_graph", output)

    return create_verb_result(cast(Table, pd.DataFrame()))
