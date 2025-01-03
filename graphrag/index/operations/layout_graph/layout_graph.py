# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing layout_graph, _run_layout and _apply_layout_to_graph methods definition."""

import networkx as nx
import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.embed_graph.typing import NodeEmbeddings
from graphrag.index.operations.layout_graph.typing import GraphLayout


def layout_graph(
    graph: nx.Graph,
    callbacks: WorkflowCallbacks,
    enabled: bool,
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
    layout = _run_layout(
        graph,
        enabled,
        embeddings if embeddings is not None else {},
        callbacks,
    )

    layout_df = pd.DataFrame(layout)
    return layout_df.loc[
        :,
        ["label", "x", "y", "size"],
    ]


def _run_layout(
    graph: nx.Graph,
    enabled: bool,
    embeddings: NodeEmbeddings,
    callbacks: WorkflowCallbacks,
) -> GraphLayout:
    if enabled:
        from graphrag.index.operations.layout_graph.umap import (
            run as run_umap,
        )

        return run_umap(
            graph,
            embeddings,
            lambda e, stack, d: callbacks.error("Error in Umap", e, stack, d),
        )
    from graphrag.index.operations.layout_graph.zero import (
        run as run_zero,
    )

    return run_zero(
        graph,
        lambda e, stack, d: callbacks.error("Error in Zero", e, stack, d),
    )
