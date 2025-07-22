# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph definition."""

import networkx as nx
import pandas as pd


def create_graph(
    edges: pd.DataFrame,
    edge_attr: list[str | int] | None = None,
    nodes: pd.DataFrame | None = None,
    node_id: str = "title",
) -> nx.Graph:
    """Create a networkx graph from nodes and edges dataframes."""
    graph = nx.from_pandas_edgelist(edges, edge_attr=edge_attr)

    if nodes is not None:
        nodes.set_index(node_id, inplace=True)
        graph.add_nodes_from((n, dict(d)) for n, d in nodes.iterrows())

    return graph
