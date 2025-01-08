# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph pruning."""

from typing import TYPE_CHECKING, cast

import graspologic as glc
import networkx as nx
import numpy as np

import graphrag.index.operations.build_noun_graph.schemas as schema

if TYPE_CHECKING:
    from networkx.classes.reportviews import DegreeView


def prune_graph(
    graph: nx.Graph,
    min_node_freq: int = 1,
    max_node_freq_std: float | None = None,
    min_edge_weight: int = 1,
    min_node_degree: int = 1,
    remove_ego_nodes: bool = False,
    max_node_degree_std: float | None = None,
    lcc_only: bool = False,
) -> nx.Graph:
    """Prune graph by removing nodes that are out of frequency/degree ranges and edges with low weights."""
    # remove ego nodes if needed
    degree = cast("DegreeView", graph.degree)
    degrees = list(degree())  # type: ignore
    if remove_ego_nodes:
        # ego node is one with highest degree
        ego_node = max(degrees, key=lambda x: x[1])
        graph.remove_nodes_from([ego_node[0]])

    # remove nodes that are not within the predefined degree range
    graph.remove_nodes_from([
        node for node, degree in degrees if degree < min_node_degree
    ])
    if max_node_degree_std is not None:
        upper_threshold = _get_upper_threshold_by_std(
            [degree for _, degree in degrees], max_node_degree_std
        )
        graph.remove_nodes_from([
            node for node, degree in degrees if degree > upper_threshold
        ])

    # remove nodes that are not within the predefined frequency range
    graph.remove_nodes_from([
        node
        for node, data in graph.nodes(data=True)
        if data[schema.NODE_FREQUENCY] < min_node_freq
    ])
    if max_node_freq_std is not None:
        upper_threshold = _get_upper_threshold_by_std(
            [data[schema.NODE_FREQUENCY] for _, data in graph.nodes(data=True)],
            max_node_freq_std,
        )
        graph.remove_nodes_from([
            node
            for node, data in graph.nodes(data=True)
            if data[schema.NODE_FREQUENCY] > upper_threshold
        ])

    # remove edges by min weight
    graph.remove_edges_from([
        (source, target)
        for source, target, data in graph.edges(data=True)
        if source in graph.nodes()
        and target in graph.nodes()
        and data[schema.EDGE_WEIGHT] < min_edge_weight
    ])

    # add degree to nodes
    for node, data in graph.nodes(data=True):
        data[schema.NODE_DEGREE] = degree(node)

    # add combined degree to edges
    # todo: this actually happens later in the normal pipeline, so we'll defer it
    # however, we may be able to streamline that generally if we update the llm based one as well and just make it an extraction output requirement
    for source, target, data in graph.edges(data=True):
        data[schema.EDGE_DEGREE] = degree(source) + degree(target)  # type: ignore

    if lcc_only:
        return glc.utils.largest_connected_component(graph)  # type: ignore

    return graph


def _get_upper_threshold_by_std(
    data: list[float] | list[int], std_trim: float
) -> float:
    """Get upper threshold by standard deviation."""
    mean = np.mean(data)
    std = np.std(data)
    return mean + std_trim * std  # type: ignore
