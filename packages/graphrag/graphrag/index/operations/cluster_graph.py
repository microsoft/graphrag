# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing cluster_graph method definition."""

import logging

import networkx as nx

from graphrag.graphs.stable_lcc import stable_lcc
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.utils.graphs import hierarchical_leiden

Communities = list[tuple[int, int, int, list[str]]]


logger = logging.getLogger(__name__)


def cluster_graph(
    graph: nx.Graph,
    max_cluster_size: int,
    use_lcc: bool,
    seed: int | None = None,
) -> Communities:
    """Apply a hierarchical clustering algorithm to a graph."""
    if len(graph.nodes) == 0:
        logger.warning("Graph has no nodes")
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
    if use_lcc:
        edges = nx.to_pandas_edgelist(graph)
        lcc_edges = stable_lcc(edges)
        edge_attrs: list[str | int] = [
            c for c in lcc_edges.columns if c not in ("source", "target")
        ]
        graph = create_graph(lcc_edges, edge_attr=edge_attrs or None)

        # Rebuild with sorted nodes so Leiden iterates them deterministically
        sorted_graph = nx.Graph()
        sorted_graph.add_nodes_from(sorted(graph.nodes(data=True), key=lambda x: x[0]))
        sorted_graph.add_edges_from(graph.edges(data=True))
        graph = sorted_graph

    community_mapping = hierarchical_leiden(
        graph, max_cluster_size=max_cluster_size, random_seed=seed
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
