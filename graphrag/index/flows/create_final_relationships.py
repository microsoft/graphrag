# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

from typing import cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.compute_edge_combined_degree import (
    compute_edge_combined_degree,
)
from graphrag.index.operations.unpack_graph import unpack_graph


def create_final_relationships(
    entity_graph: pd.DataFrame,
    nodes: pd.DataFrame,
    callbacks: VerbCallbacks,
) -> pd.DataFrame:
    """All the steps to transform final relationships."""
    graph_edges = unpack_graph(entity_graph, callbacks, "clustered_graph", "edges")

    graph_edges.rename(columns={"source_id": "text_unit_ids"}, inplace=True)

    filtered = cast(
        pd.DataFrame, graph_edges[graph_edges["level"] == 0].reset_index(drop=True)
    )

    pruned_edges = filtered.drop(columns=["level"])

    filtered_nodes = nodes[nodes["level"] == 0].reset_index(drop=True)
    filtered_nodes = cast(pd.DataFrame, filtered_nodes[["title", "degree"]])

    edge_combined_degree = compute_edge_combined_degree(
        pruned_edges,
        filtered_nodes,
        to="rank",
        node_name_column="title",
        node_degree_column="degree",
        edge_source_column="source",
        edge_target_column="target",
    )

    edge_combined_degree["human_readable_id"] = edge_combined_degree[
        "human_readable_id"
    ].astype(str)
    edge_combined_degree["text_unit_ids"] = edge_combined_degree[
        "text_unit_ids"
    ].str.split(",")

    # TODO: Find duplication source
    return edge_combined_degree.drop_duplicates(subset=["source", "target"])
