#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Networkx load_graph utility definition."""

import networkx as nx


def load_graph(graphml: str | nx.Graph) -> nx.Graph:
    """Load a graph from a graphml file or a networkx graph."""
    return nx.parse_graphml(graphml) if isinstance(graphml, str) else graphml
