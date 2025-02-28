# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _create_node_position methods definitions."""

import logging
import traceback

import networkx as nx

from graphrag.index.operations.layout_graph.typing import (
    GraphLayout,
    NodePosition,
)
from graphrag.index.typing.error_handler import ErrorHandlerFn

# TODO: This could be handled more elegantly, like what columns to use
# for "size" or "cluster"
# We could also have a boolean to indicate to use node sizes or clusters

log = logging.getLogger(__name__)


def run(
    graph: nx.Graph,
    on_error: ErrorHandlerFn,
) -> GraphLayout:
    """Run method definition."""
    node_clusters = []
    node_sizes = []

    nodes = list(graph.nodes)

    for node_id in nodes:
        node = graph.nodes[node_id]
        cluster = node.get("cluster", node.get("community", -1))
        node_clusters.append(cluster)
        size = node.get("degree", node.get("size", 0))
        node_sizes.append(size)

    additional_args = {}
    if len(node_clusters) > 0:
        additional_args["node_categories"] = node_clusters
    if len(node_sizes) > 0:
        additional_args["node_sizes"] = node_sizes

    try:
        return get_zero_positions(node_labels=nodes, **additional_args)
    except Exception as e:
        log.exception("Error running zero-position")
        on_error(e, traceback.format_exc(), None)
        # Umap may fail due to input sparseness or memory pressure.
        # For now, in these cases, we'll just return a layout with all nodes at (0, 0)
        result = []
        for i in range(len(nodes)):
            cluster = node_clusters[i] if len(node_clusters) > 0 else 1
            result.append(
                NodePosition(x=0, y=0, label=nodes[i], size=0, cluster=str(cluster))
            )
        return result


def get_zero_positions(
    node_labels: list[str],
    node_categories: list[int] | None = None,
    node_sizes: list[int] | None = None,
    three_d: bool | None = False,
) -> list[NodePosition]:
    """Project embedding vectors down to 2D/3D using UMAP."""
    embedding_position_data: list[NodePosition] = []
    for index, node_name in enumerate(node_labels):
        node_category = 1 if node_categories is None else node_categories[index]
        node_size = 1 if node_sizes is None else node_sizes[index]

        if not three_d:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=0,
                    y=0,
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
        else:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=0,
                    y=0,
                    z=0,
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
    return embedding_position_data
