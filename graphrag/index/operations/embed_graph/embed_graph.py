# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embed_graph and run_embeddings methods definition."""

from typing import Any

import networkx as nx

from graphrag.index.operations.embed_graph.embed_node2vec import embed_node2vec
from graphrag.index.operations.embed_graph.typing import (
    EmbedGraphStrategyType,
    NodeEmbeddings,
)
from graphrag.index.utils.load_graph import load_graph
from graphrag.index.utils.stable_lcc import stable_largest_connected_component


def embed_graph(
    graph: nx.Graph,
    strategy: dict[str, Any],
) -> NodeEmbeddings:
    """
    Embed a graph into a vector space. The graph is expected to be in nx.Graph format. The operation outputs a mapping between node name and vector.

    ## Usage
    ```yaml
    args:
        strategy: <strategy config> # See strategies section below
    ```

    ## Strategies
    The embed_graph operation uses a strategy to embed the graph. The strategy is an object which defines the strategy to use. The following strategies are available:

    ### node2vec
    This strategy uses the node2vec algorithm to embed a graph. The strategy config is as follows:

    ```yaml
    strategy:
        type: node2vec
        dimensions: 1536 # Optional, The number of dimensions to use for the embedding, default: 1536
        num_walks: 10 # Optional, The number of walks to use for the embedding, default: 10
        walk_length: 40 # Optional, The walk length to use for the embedding, default: 40
        window_size: 2 # Optional, The window size to use for the embedding, default: 2
        iterations: 3 # Optional, The number of iterations to use for the embedding, default: 3
        random_seed: 86 # Optional, The random seed to use for the embedding, default: 86
    ```
    """
    strategy_type = strategy.get("type", EmbedGraphStrategyType.node2vec)
    strategy_args = {**strategy}

    return run_embeddings(strategy_type, graph, strategy_args)


def run_embeddings(
    strategy: EmbedGraphStrategyType,
    graphml_or_graph: str | nx.Graph,
    args: dict[str, Any],
) -> NodeEmbeddings:
    """Run embeddings method definition."""
    graph = load_graph(graphml_or_graph)
    match strategy:
        case EmbedGraphStrategyType.node2vec:
            return run_node_2_vec(graph, args)
        case _:
            msg = f"Unknown strategy {strategy}"
            raise ValueError(msg)


def run_node_2_vec(graph: nx.Graph, args: dict[str, Any]) -> NodeEmbeddings:
    """Run method definition."""
    if args.get("use_lcc", True):
        graph = stable_largest_connected_component(graph)

    # create graph embedding using node2vec
    embeddings = embed_node2vec(
        graph=graph,
        dimensions=args.get("dimensions", 1536),
        num_walks=args.get("num_walks", 10),
        walk_length=args.get("walk_length", 40),
        window_size=args.get("window_size", 2),
        iterations=args.get("iterations", 3),
        random_seed=args.get("random_seed", 86),
    )

    pairs = zip(embeddings.nodes, embeddings.embeddings.tolist(), strict=True)
    sorted_pairs = sorted(pairs, key=lambda x: x[0])

    return dict(sorted_pairs)
