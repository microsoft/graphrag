# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _create_node_position methods definitions."""

import logging
import traceback
from typing import Any

import networkx as nx
import numpy as np

from graphrag.index.graph.visualization import (
    GraphLayout,
    NodePosition,
    compute_umap_positions,
)
from graphrag.index.operations.embed_graph import NodeEmbeddings
from graphrag.index.typing import ErrorHandlerFn

# TODO: This could be handled more elegantly, like what columns to use
# for "size" or "cluster"
# We could also have a boolean to indicate to use node sizes or clusters

log = logging.getLogger(__name__)


def run(
    graph: nx.Graph,
    embeddings: NodeEmbeddings,
    args: dict[str, Any],
    on_error: ErrorHandlerFn,
) -> GraphLayout:
    """Run method definition."""
    node_clusters = []
    node_sizes = []

    embeddings = _filter_raw_embeddings(embeddings)
    nodes = list(embeddings.keys())
    embedding_vectors = [embeddings[node_id] for node_id in nodes]

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
        return compute_umap_positions(
            embedding_vectors=np.array(embedding_vectors),
            node_labels=nodes,
            **additional_args,
            min_dist=args.get("min_dist", 0.75),
            n_neighbors=args.get("n_neighbors", 5),
        )
    except Exception as e:
        log.exception("Error running UMAP")
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


def _filter_raw_embeddings(embeddings: NodeEmbeddings) -> NodeEmbeddings:
    return {
        node_id: embedding
        for node_id, embedding in embeddings.items()
        if embedding is not None
    }
