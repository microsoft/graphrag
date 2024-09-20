# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final nodes."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.verbs.graph.layout.layout_graph import layout_graph_df
from graphrag.index.verbs.graph.unpack import unpack_graph_df


@verb(name="create_final_nodes", treats_input_tables_as_immutable=True)
def create_final_nodes(
    input: VerbInput,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    level_for_node_positions: int,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final nodes."""
    table = cast(pd.DataFrame, input.get_input())

    laid_out_entity_graph = cast(
        pd.DataFrame,
        layout_graph_df(
            table,
            callbacks,
            strategy,
            embeddings_column="embeddings",
            graph_column="clustered_graph",
            to="node_positions",
            graph_to="positioned_graph",
        ),
    )

    nodes = cast(
        pd.DataFrame,
        unpack_graph_df(
            laid_out_entity_graph, callbacks, column="positioned_graph", type="nodes"
        ),
    )

    nodes_without_positions = nodes.drop(columns=["x", "y"])

    nodes = nodes[nodes["level"] == level_for_node_positions].reset_index(drop=True)
    nodes = cast(pd.DataFrame, nodes[["id", "x", "y"]])

    # TODO: original workflow saved an optional snapshot of top level nodes
    # Combining the verbs loses the `storage` injection, so it would fail
    # verb arg: snapshot_top_level_nodes: bool,
    # (name: "top_level_nodes", formats: ["json"])

    nodes.rename(columns={"id": "top_level_node_id"}, inplace=True)
    nodes["top_level_node_id"] = nodes["top_level_node_id"].astype(str)

    joined = nodes_without_positions.merge(
        nodes,
        left_on="id",
        right_on="top_level_node_id",
        how="inner",
    )
    joined.rename(columns={"label": "title", "cluster": "community"}, inplace=True)

    return create_verb_result(
        cast(
            Table,
            joined,
        )
    )
