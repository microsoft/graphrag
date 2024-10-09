# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.embed_graph import embed_graph
from graphrag.index.operations.snapshot_rows import snapshot_rows
from graphrag.index.storage import PipelineStorage


async def create_base_entity_graph(
    entities: pd.DataFrame,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    clustering_strategy: dict[str, Any],
    embedding_strategy: dict[str, Any] | None,
    graphml_snapshot_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to create the base entity graph."""
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

    if embedding_strategy:
        clustered["embeddings"] = await embed_graph(
            clustered,
            callbacks,
            column="clustered_graph",
            strategy=embedding_strategy,
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
    if embedding_strategy:
        final_columns.append("embeddings")

    return cast(pd.DataFrame, clustered[final_columns])
