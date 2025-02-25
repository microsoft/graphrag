# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph definition."""

import networkx as nx
import pandas as pd


def graph_to_dataframes(
    graph: nx.Graph,
    node_columns: list[str] | None = None,
    edge_columns: list[str] | None = None,
    node_id: str = "title",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deconstructs an nx.Graph into nodes and edges dataframes."""
    # nx graph nodes are a tuple, and creating a df from them results in the id being the index
    nodes = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient="index")
    nodes[node_id] = nodes.index
    nodes.reset_index(inplace=True, drop=True)

    edges = nx.to_pandas_edgelist(graph)

    if node_columns:
        nodes = nodes.loc[:, node_columns]

    if edge_columns:
        edges = edges.loc[:, edge_columns]

    return (nodes, edges)
