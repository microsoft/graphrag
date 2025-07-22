# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embed_graph and run_embeddings methods definition."""

import networkx as nx

from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.index.operations.embed_graph.embed_node2vec import embed_node2vec
from graphrag.index.operations.embed_graph.typing import (
    NodeEmbeddings,
)
from graphrag.index.utils.stable_lcc import stable_largest_connected_component


def embed_graph(
    graph: nx.Graph,
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

    # create graph embedding using node2vec
    embeddings = embed_node2vec(
        graph=graph,
        dimensions=config.dimensions,
        num_walks=config.num_walks,
        walk_length=config.walk_length,
        window_size=config.window_size,
        iterations=config.iterations,
        random_seed=config.random_seed,
    )

    pairs = zip(embeddings.nodes, embeddings.embeddings.tolist(), strict=True)
    sorted_pairs = sorted(pairs, key=lambda x: x[0])

    return dict(sorted_pairs)
