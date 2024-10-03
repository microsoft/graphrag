# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.snapshot_rows import snapshot_rows
from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.graph.embed.embed_graph import embed_graph_df


async def create_base_entity_graph(
    entities: pd.DataFrame,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    clustering_config: dict[str, Any],
    embedding_config: dict[str, Any],
    graphml_snapshot_enabled: bool = False,
    embed_graph_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to create the base entity graph."""
    clustering_strategy = clustering_config.get("strategy", {"type": "leiden"})

    clustered = cluster_graph(
        entities,
        callbacks,
        column="entity_graph",
        strategy=clustering_strategy,
        to="clustered_graph",
        level_to="level",
    )

    if graphml_snapshot_enabled:
        await snapshot_rows(
            clustered,
            column="clustered_graph",
            base_name="clustered_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    embedding_strategy = embedding_config.get("strategy")
    if embed_graph_enabled and embedding_strategy:
        clustered = await embed_graph_df(
            clustered,
            callbacks,
            column="clustered_graph",
            strategy=embedding_strategy,
            to="embeddings",
        )

    # take second snapshot after embedding
    # todo: this could be skipped if embedding isn't performed, other wise it is a copy of the regular graph?
    if graphml_snapshot_enabled:
        await snapshot_rows(
            clustered,
            column="entity_graph",
            base_name="embedded_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    final_columns = ["level", "clustered_graph"]
    if embed_graph_enabled:
        final_columns.append("embeddings")

    return cast(pd.DataFrame, clustered[final_columns])
