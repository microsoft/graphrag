# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing layout_graph, _run_layout and _apply_layout_to_graph methods definition."""

from enum import Enum
from typing import Any

import networkx as nx
import pandas as pd
from datashaper import VerbCallbacks

from graphrag.index.graph.visualization import GraphLayout
from graphrag.index.operations.embed_graph import NodeEmbeddings


class LayoutGraphStrategyType(str, Enum):
    """LayoutGraphStrategyType class definition."""

    umap = "umap"
    zero = "zero"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


def layout_graph(
    graph: nx.Graph,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    embeddings: NodeEmbeddings | None,
):
    """
    Apply a layout algorithm to a nx.Graph. The method returns a dataframe containing the node positions.

    ## Usage
    ```yaml
    args:
        graph: The nx.Graph to layout
        embeddings: Embeddings for each node in the graph
        strategy: <strategy config> # See strategies section below
    ```

    ## Strategies
    The layout graph verb uses a strategy to layout the graph. The strategy is a json object which defines the strategy to use. The following strategies are available:

    ### umap
    This strategy uses the umap algorithm to layout a graph. The strategy config is as follows:
    ```yaml
    strategy:
        type: umap
        n_neighbors: 5 # Optional, The number of neighbors to use for the umap algorithm, default: 5
        min_dist: 0.75 # Optional, The min distance to use for the umap algorithm, default: 0.75
    ```
    """
    strategy_type = strategy.get("type", LayoutGraphStrategyType.umap)
    strategy_args = {**strategy}

    layout = _run_layout(
        strategy_type,
        graph,
        embeddings if embeddings is not None else {},
        strategy_args,
        callbacks,
    )

    layout_df = pd.DataFrame(layout)
    return layout_df.loc[
        :,
        ["label", "x", "y", "size"],
    ]


def _run_layout(
    strategy: LayoutGraphStrategyType,
    graph: nx.Graph,
    embeddings: NodeEmbeddings,
    args: dict[str, Any],
    callbacks: VerbCallbacks,
) -> GraphLayout:
    match strategy:
        case LayoutGraphStrategyType.umap:
            from graphrag.index.operations.layout_graph.methods.umap import (
                run as run_umap,
            )

            return run_umap(
                graph,
                embeddings,
                args,
                lambda e, stack, d: callbacks.error("Error in Umap", e, stack, d),
            )
        case LayoutGraphStrategyType.zero:
            from graphrag.index.operations.layout_graph.methods.zero import (
                run as run_zero,
            )

            return run_zero(
                graph,
                args,
                lambda e, stack, d: callbacks.error("Error in Zero", e, stack, d),
            )
        case _:
            msg = f"Unknown strategy {strategy}"
            raise ValueError(msg)
