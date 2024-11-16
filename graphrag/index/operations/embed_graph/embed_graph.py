# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embed_graph and run_embeddings methods definition."""

from enum import Enum
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import VerbCallbacks, derive_from_rows

from graphrag.index.graph.embedding import embed_nod2vec
from graphrag.index.graph.utils import stable_largest_connected_component
from graphrag.index.operations.embed_graph.typing import NodeEmbeddings
from graphrag.index.utils.load_graph import load_graph


class EmbedGraphStrategyType(str, Enum):
    """EmbedGraphStrategyType class definition."""

    node2vec = "node2vec"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


async def embed_graph(
    input: pd.DataFrame,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    column: str,
    num_threads: int = 4,
):
    """
    Embed a graph into a vector space. The graph is expected to be in graphml format. The operation outputs a new column containing a mapping between node_id and vector.

    ## Usage
    ```yaml
    args:
        column: clustered_graph # The name of the column containing the graph, should be a graphml graph
        to: embeddings # The name of the column to output the embeddings to
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

    async def run_strategy(row):  # noqa RUF029 async is required for interface
        return run_embeddings(strategy_type, cast(Any, row[column]), strategy_args)

    results = await derive_from_rows(
        input,
        run_strategy,
        callbacks=callbacks,
        num_threads=num_threads,
    )

    return list(results)


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
    embeddings = embed_nod2vec(
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
