# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embed_graph and run_embeddings methods definition."""

import networkx as nx
import pandas as pd

from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.index.operations.embed_graph.embed_gee import embed_gee
from graphrag.index.operations.embed_graph.typing import (
    NodeEmbeddings,
)
from graphrag.index.utils.stable_lcc import stable_largest_connected_component


def embed_graph(
    graph: nx.Graph,
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    config: EmbedGraphConfig,
) -> NodeEmbeddings:
    """
    Embed a graph into a vector space using node2vec. The graph is expected to be in nx.Graph format. The operation outputs a mapping between node name and vector.

    ## Usage
    ```yaml
    dimensions: 1536 # Optional, The number of dimensions to use for the embedding, default: 1536
    num_walks: 10 # Optional, The number of walks to use for the embedding, default: 10
    walk_length: 40 # Optional, The walk length to use for the embedding, default: 40
    window_size: 2 # Optional, The window size to use for the embedding, default: 2
    iterations: 3 # Optional, The number of iterations to use for the embedding, default: 3
    random_seed: 86 # Optional, The random seed to use for the embedding, default: 86
    ```
    """
    if config.use_lcc:
        graph = stable_largest_connected_component(graph)

    # gee requires a cluster label for each entity
    clusters = communities.explode("entity_ids")
    labeled = entities.merge(
        clusters[["entity_ids", "community", "level"]],
        left_on="id",
        right_on="entity_ids",
        how="left",
    )
    labeled = labeled[labeled["community"].notna()]
    labeled["community"] = labeled["community"].astype(int)
    labeled["level"] = labeled["level"].astype(int)

    # gee needs a complete hierarchy for the clusters - we'll "fill down" using parent if a node is missing at lower levels
    max_level = labeled["level"].max()

    node_to_label = {}
    for node in labeled.itertuples():
        for level in range(node.level, max_level + 1):
            node_labels = node_to_label.get(node.title, {})
            node_labels[level] = node.community
            node_to_label[node.title] = node_labels

    vectors = embed_gee(
        graph=graph,
        node_to_label=node_to_label,
        correlation=True,
        diag_a=True,
        laplacian=True,
        max_level=max_level,
    )

    node_list = sorted(node_to_label.keys())
    return dict(zip(node_list, vectors, strict=True))
