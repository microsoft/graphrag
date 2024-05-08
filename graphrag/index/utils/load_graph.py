# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Networkx load_graph utility definition."""

import networkx as nx


def load_graph(graphml: str | nx.Graph) -> nx.Graph:
    """Load a graph from a graphml file or a networkx graph."""
    return nx.parse_graphml(graphml) if isinstance(graphml, str) else graphml
