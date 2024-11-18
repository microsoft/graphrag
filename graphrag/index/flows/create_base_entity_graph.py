# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.embed_graph import embed_graph
from graphrag.index.operations.extract_entities import extract_entities
from graphrag.index.operations.merge_graphs import merge_graphs
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.index.operations.snapshot_rows import snapshot_rows
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage


async def create_base_entity_graph(
    text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    clustering_strategy: dict[str, Any],
    extraction_strategy: dict[str, Any] | None = None,
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
) -> pd.DataFrame:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    entities, entity_graphs = await extract_entities(
        text_units,
        callbacks,
        cache,
        text_column="text",
        id_column="id",
        strategy=extraction_strategy,
        async_mode=extraction_async_mode,
        entity_types=entity_types,
        to="entities",
        num_threads=extraction_num_threads,
    )

    merged_graph = merge_graphs(
        entity_graphs,
        callbacks,
        node_operations=node_merge_config,
        edge_operations=edge_merge_config,
    )

    summarized = await summarize_descriptions(
        merged_graph,
        callbacks,
        cache,
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )

    clustered = cluster_graph(
        summarized,
        callbacks,
        column="entity_graph",
        strategy=clustering_strategy,
        to="clustered_graph",
        level_to="level",
    )

    if embedding_strategy:
        clustered["embeddings"] = await embed_graph(
            clustered,
            callbacks,
            column="clustered_graph",
            strategy=embedding_strategy,
        )

    if snapshot_raw_entities_enabled:
        await snapshot(
            entities,
            name="raw_extracted_entities",
            storage=storage,
            formats=["json"],
        )

    if snapshot_graphml_enabled:
        await snapshot_graphml(
            merged_graph,
            name="merged_graph",
            storage=storage,
        )
        await snapshot_graphml(
            summarized,
            name="summarized_graph",
            storage=storage,
        )
        await snapshot_rows(
            clustered,
            column="clustered_graph",
            base_name="clustered_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )
        if embedding_strategy:
            await snapshot_rows(
                clustered,
                column="entity_graph",
                base_name="embedded_graph",
                storage=storage,
                formats=[{"format": "text", "extension": "graphml"}],
            )

    final_columns = ["level", "clustered_graph"]
    if embedding_strategy:
        final_columns.append("embeddings")

    output = cast(pd.DataFrame, clustered[final_columns])

    if snapshot_transient_enabled:
        await snapshot(
            output,
            name="create_base_entity_graph",
            storage=storage,
            formats=["parquet"],
        )

    return output
