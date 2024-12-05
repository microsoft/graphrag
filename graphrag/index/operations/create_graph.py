# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph definition."""

import networkx as nx
import pandas as pd


def create_graph(edges_df: pd.DataFrame) -> nx.Graph:
    """Create a networkx graph from nodes and edges dataframes."""
    return nx.from_pandas_edgelist(edges_df)
