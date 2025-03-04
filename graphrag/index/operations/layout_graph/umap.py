# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _create_node_position methods definitions."""

import logging
import traceback

import networkx as nx
import numpy as np

from graphrag.index.operations.embed_graph.typing import NodeEmbeddings
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
    embeddings: NodeEmbeddings,
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


def compute_umap_positions(
    embedding_vectors: np.ndarray,
    node_labels: list[str],
    node_categories: list[int] | None = None,
    node_sizes: list[int] | None = None,
    min_dist: float = 0.75,
    n_neighbors: int = 5,
    spread: int = 1,
    metric: str = "euclidean",
    n_components: int = 2,
    random_state: int = 86,
) -> list[NodePosition]:
    """Project embedding vectors down to 2D/3D using UMAP."""
    # NOTE: This import is done here to reduce the initial import time of the graphrag package
    import umap

    embedding_positions = umap.UMAP(
        min_dist=min_dist,
        n_neighbors=n_neighbors,
        spread=spread,
        n_components=n_components,
        metric=metric,
        random_state=random_state,
    ).fit_transform(embedding_vectors)

    embedding_position_data: list[NodePosition] = []
    for index, node_name in enumerate(node_labels):
        node_points = embedding_positions[index]  # type: ignore
        node_category = 1 if node_categories is None else node_categories[index]
        node_size = 1 if node_sizes is None else node_sizes[index]

        if len(node_points) == 2:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=float(node_points[0]),
                    y=float(node_points[1]),
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
        else:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=float(node_points[0]),
                    y=float(node_points[1]),
                    z=float(node_points[2]),
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
    return embedding_position_data
