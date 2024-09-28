# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.storage import PipelineStorage
from graphrag.index.verbs.graph.clustering.cluster_graph import cluster_graph_df
from graphrag.index.verbs.graph.embed.embed_graph import embed_graph_df
from graphrag.index.verbs.snapshot_rows import snapshot_rows_df


@verb(
    name="create_base_entity_graph",
    treats_input_tables_as_immutable=True,
)
async def create_base_entity_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    clustering_config: dict[str, Any],
    embedding_config: dict[str, Any],
    graphml_snapshot_enabled: bool = False,
    embed_graph_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast(pd.DataFrame, input.get_input())

    clustering_strategy = clustering_config.get("strategy", {"type": "leiden"})

    clustered = cluster_graph_df(
        source,
        callbacks,
        column="entity_graph",
        strategy=clustering_strategy,
        to="clustered_graph",
        level_to="level",
    )

    if graphml_snapshot_enabled:
        await snapshot_rows_df(
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
        await snapshot_rows_df(
            clustered,
            column="entity_graph",
            base_name="embedded_graph",
            storage=storage,
            formats=[{"format": "text", "extension": "graphml"}],
        )

    final_columns = ["level", "clustered_graph"]
    if embed_graph_enabled:
        final_columns.append("embeddings")

    return create_verb_result(cast(Table, clustered[final_columns]))
