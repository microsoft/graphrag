# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing layout_graph, _run_layout and _apply_layout_to_graph methods definition."""

from enum import Enum
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import VerbCallbacks, progress_callback

from graphrag.index.graph.visualization import GraphLayout
from graphrag.index.operations.embed_graph import NodeEmbeddings
from graphrag.index.utils.load_graph import load_graph


class LayoutGraphStrategyType(str, Enum):
    """LayoutGraphStrategyType class definition."""

    umap = "umap"
    zero = "zero"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


def layout_graph(
    input_df: pd.DataFrame,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    embeddings_column: str,
    graph_column: str,
    to: str,
    graph_to: str | None = None,
):
    """
    Apply a layout algorithm to a graph. The graph is expected to be in graphml format. The verb outputs a new column containing the laid out graph.

    ## Usage
    ```yaml
    args:
        graph_column: clustered_graph # The name of the column containing the graph, should be a graphml graph
        embeddings_column: embeddings # The name of the column containing the embeddings
        to: node_positions # The name of the column to output the node positions to
        graph_to: positioned_graph # The name of the column to output the positioned graph to
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
    output_df = input_df
    num_items = len(output_df)
    strategy_type = strategy.get("type", LayoutGraphStrategyType.umap)
    strategy_args = {**strategy}

    has_embeddings = embeddings_column in output_df.columns

    layouts = output_df.apply(
        progress_callback(
            lambda row: _run_layout(
                strategy_type,
                row[graph_column],
                row[embeddings_column] if has_embeddings else {},
                strategy_args,
                callbacks,
            ),
            callbacks.progress,
            num_items,
        ),
        axis=1,
    )
    output_df[to] = layouts.apply(lambda layout: [pos.to_pandas() for pos in layout])
    if graph_to is not None:
        output_df[graph_to] = output_df.apply(
            lambda row: _apply_layout_to_graph(
                row[graph_column], cast(GraphLayout, layouts[row.name])
            ),
            axis=1,
        )
    return output_df


def _run_layout(
    strategy: LayoutGraphStrategyType,
    graphml_or_graph: str | nx.Graph,
    embeddings: NodeEmbeddings,
    args: dict[str, Any],
    callbacks: VerbCallbacks,
) -> GraphLayout:
    graph = load_graph(graphml_or_graph)
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


def _apply_layout_to_graph(
    graphml_or_graph: str | nx.Graph, layout: GraphLayout
) -> str:
    graph = load_graph(graphml_or_graph)
    for node_position in layout:
        if node_position.label in graph.nodes:
            graph.nodes[node_position.label]["x"] = node_position.x
            graph.nodes[node_position.label]["y"] = node_position.y
            graph.nodes[node_position.label]["size"] = node_position.size
    return "\n".join(nx.generate_graphml(graph))
