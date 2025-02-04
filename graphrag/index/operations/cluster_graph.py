# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing cluster_graph, apply_clustering and run_layout methods definition."""

import logging

import networkx as nx

from graphrag.index.utils.stable_lcc import stable_largest_connected_component

Communities = list[tuple[int, int, int, list[str]]]


log = logging.getLogger(__name__)


def cluster_graph(
    graph: nx.Graph,
    max_cluster_size: int,
    use_lcc: bool,
    seed: int | None = None,
) -> Communities:
    """Apply a hierarchical clustering algorithm to a graph."""
    if len(graph.nodes) == 0:
        log.warning("Graph has no nodes")
        return []

    node_id_to_community_map, parent_mapping = _compute_leiden_communities(
        graph=graph,
        max_cluster_size=max_cluster_size,
        use_lcc=use_lcc,
        seed=seed,
    )

    levels = sorted(node_id_to_community_map.keys())

    clusters: dict[int, dict[int, list[str]]] = {}
    for level in levels:
        result = {}
        clusters[level] = result
        for node_id, raw_community_id in node_id_to_community_map[level].items():
            community_id = raw_community_id
            if community_id not in result:
                result[community_id] = []
            result[community_id].append(node_id)

    results: Communities = []
    for level in clusters:
        for cluster_id, nodes in clusters[level].items():
            results.append((level, cluster_id, parent_mapping[cluster_id], nodes))
    return results


# Taken from graph_intelligence & adapted
def _compute_leiden_communities(
    graph: nx.Graph | nx.DiGraph,
    max_cluster_size: int,
    use_lcc: bool,
    seed: int | None = None,
) -> tuple[dict[int, dict[str, int]], dict[int, int]]:
    """Return Leiden root communities and their hierarchy mapping."""
    # NOTE: This import is done here to reduce the initial import time of the graphrag package
    from graspologic_native import hierarchical_leiden
    # from graspologic.partition import hierarchical_leiden

    if use_lcc:
        graph = stable_largest_connected_component(graph)

    community_mapping = hierarchical_leiden(
        edges=_nx_to_edge_list(graph),
        max_cluster_size=max_cluster_size,
        seed=seed,
        starting_communities=None,
        resolution=1.0,
        randomness=0.001,
        use_modularity=True,
        iterations=0,
    )

    results: dict[int, dict[str, int]] = {}
    hierarchy: dict[int, int] = {}
    for partition in community_mapping:
        results[partition.level] = results.get(partition.level, {})
        results[partition.level][partition.node] = partition.cluster

        hierarchy[partition.cluster] = (
            partition.parent_cluster if partition.parent_cluster is not None else -1
        )

    return results, hierarchy


def _nx_to_edge_list(
    graph: nx.Graph,
    weight_attribute: str = "weight",
    weight_default: float = 1.0,
) -> list[tuple[str, str, float]]:
    """
    Convert an undirected, non-multigraph networkx graph to a list of edges,
    where each edge is a tuple of (source_str, target_str, weight).
    """

    # Validate graph type: must be undirected and not a multigraph
    if graph.is_directed() or graph.is_multigraph():
        raise ValueError(
            "Only undirected non-multi-graph networkx graphs are supported."
        )

    edge_list: list[tuple[str, str, float]] = []

    # Decide how to retrieve the weight data
    edge_iter = graph.edges(data=weight_attribute, default=weight_default)  # type: ignore

    for source, target, weight in edge_iter:
        source_str = str(source)
        target_str = str(target)
        edge_list.append((source_str, target_str, float(weight)))

    return edge_list
