# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing normalize_node_names method definition."""

import html

import networkx as nx


def normalize_node_names(graph: nx.Graph | nx.DiGraph) -> nx.Graph | nx.DiGraph:
    """Normalize node names."""
    node_mapping = {node: html.unescape(node.upper().strip()) for node in graph.nodes()}  # type: ignore
    return nx.relabel_nodes(graph, node_mapping)
