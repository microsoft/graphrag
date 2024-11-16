# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final nodes."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.layout_graph import layout_graph
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.operations.unpack_graph import unpack_graph
from graphrag.index.storage.pipeline_storage import PipelineStorage


async def create_final_nodes(
    entity_graph: pd.DataFrame,
    callbacks: VerbCallbacks,
    storage: PipelineStorage,
    layout_strategy: dict[str, Any],
    level_for_node_positions: int,
    snapshot_top_level_nodes_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to transform final nodes."""
    laid_out_entity_graph = cast(
        pd.DataFrame,
        layout_graph(
            entity_graph,
            callbacks,
            layout_strategy,
            embeddings_column="embeddings",
            graph_column="clustered_graph",
            to="node_positions",
            graph_to="positioned_graph",
        ),
    )

    nodes = cast(
        pd.DataFrame,
        unpack_graph(
            laid_out_entity_graph, callbacks, column="positioned_graph", type="nodes"
        ),
    )

    nodes_without_positions = nodes.drop(columns=["x", "y"])

    nodes = nodes[nodes["level"] == level_for_node_positions].reset_index(drop=True)
    nodes = cast(pd.DataFrame, nodes[["id", "x", "y"]])

    if snapshot_top_level_nodes_enabled:
        await snapshot(
            nodes,
            name="top_level_nodes",
            storage=storage,
            formats=["json"],
        )

    joined = nodes_without_positions.merge(
        nodes,
        on="id",
        how="inner",
    )
    joined.rename(columns={"label": "title", "cluster": "community"}, inplace=True)
    joined["community"] = joined["community"].fillna(-1).astype(int)

    # drop anything that isn't graph-related or needing to be preserved
    # the rest can be looked up on the canonical entities table
    joined.drop(
        columns=["source_id", "type", "description", "size", "graph_embedding"],
        inplace=True,
    )

    deduped = joined.drop_duplicates(subset=["title", "community"])
    return deduped.loc[
        :,
        [
            "id",
            "human_readable_id",
            "title",
            "community",
            "level",
            "degree",
            "x",
            "y",
        ],
    ]
