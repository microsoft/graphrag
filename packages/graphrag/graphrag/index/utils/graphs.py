# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Collection of graph utility functions.

These are largely copies/re-implementations of graspologic methods to avoid dependency issues.
"""

import logging
import math
from collections import defaultdict
from typing import Any, cast

import graspologic_native as gn
import networkx as nx
import numpy as np
import pandas as pd

from graphrag.config.enums import ModularityMetric

logger = logging.getLogger(__name__)


def largest_connected_component(graph: nx.Graph) -> nx.Graph:
    """Return the largest connected component of the graph."""
    graph = graph.copy()
    lcc_nodes = max(nx.connected_components(graph), key=len)
    lcc = graph.subgraph(lcc_nodes).copy()
    lcc.remove_nodes_from([n for n in lcc if n not in lcc_nodes])
    return cast("nx.Graph", lcc)


def _nx_to_edge_list(
    graph: nx.Graph,
    weight_attribute: str = "weight",
    weight_default: float = 1.0,
) -> list[tuple[str, str, float]]:
    """
    Convert an undirected, non-multigraph networkx graph to a list of edges.

    Each edge is represented as a tuple of (source_str, target_str, weight).
    """
    edge_list: list[tuple[str, str, float]] = []

    # Decide how to retrieve the weight data
    edge_iter = graph.edges(data=weight_attribute, default=weight_default)  # type: ignore

    for source, target, weight in edge_iter:
        source_str = str(source)
        target_str = str(target)
        edge_list.append((source_str, target_str, float(weight)))

    return edge_list


def hierarchical_leiden(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int | None = 0xDEADBEEF,
) -> list[gn.HierarchicalCluster]:
    """Run hierarchical leiden on the graph."""
    return gn.hierarchical_leiden(
        edges=_nx_to_edge_list(graph),
        max_cluster_size=max_cluster_size,
        seed=random_seed,
        starting_communities=None,
        resolution=1.0,
        randomness=0.001,
        use_modularity=True,
        iterations=1,
    )


def modularity(
    graph: nx.Graph,
    partitions: dict[Any, int],
    weight_attribute: str = "weight",
    resolution: float = 1.0,
) -> float:
    """Given an undirected graph and a dictionary of vertices to community ids, calculate the modularity."""
    components = _modularity_components(graph, partitions, weight_attribute, resolution)
    return sum(components.values())


def _modularity_component(
    intra_community_degree: float,
    total_community_degree: float,
    network_degree_sum: float,
    resolution: float,
) -> float:
    community_degree_ratio = math.pow(total_community_degree, 2.0) / (
        2.0 * network_degree_sum
    )
    return (intra_community_degree - resolution * community_degree_ratio) / (
        2.0 * network_degree_sum
    )


def _modularity_components(
    graph: nx.Graph,
    partitions: dict[Any, int],
    weight_attribute: str = "weight",
    resolution: float = 1.0,
) -> dict[int, float]:
    total_edge_weight = 0.0
    communities = set(partitions.values())

    degree_sums_within_community: dict[int, float] = defaultdict(lambda: 0.0)
    degree_sums_for_community: dict[int, float] = defaultdict(lambda: 0.0)
    for vertex, neighbor_vertex, weight in graph.edges(data=weight_attribute):
        vertex_community = partitions[vertex]
        neighbor_community = partitions[neighbor_vertex]
        if vertex_community == neighbor_community:
            if vertex == neighbor_vertex:
                degree_sums_within_community[vertex_community] += weight
            else:
                degree_sums_within_community[vertex_community] += weight * 2.0
        degree_sums_for_community[vertex_community] += weight
        degree_sums_for_community[neighbor_community] += weight
        total_edge_weight += weight

    return {
        comm: _modularity_component(
            degree_sums_within_community[comm],
            degree_sums_for_community[comm],
            total_edge_weight,
            resolution,
        )
        for comm in communities
    }


def calculate_root_modularity(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
) -> float:
    """Calculate distance between the modularity of the graph's root clusters and the target modularity."""
    hcs = hierarchical_leiden(
        graph, max_cluster_size=max_cluster_size, random_seed=random_seed
    )
    root_clusters = first_level_hierarchical_clustering(hcs)
    return modularity(graph, root_clusters)


def calculate_leaf_modularity(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
) -> float:
    """Calculate distance between the modularity of the graph's leaf clusters and the target modularity."""
    hcs = hierarchical_leiden(
        graph, max_cluster_size=max_cluster_size, random_seed=random_seed
    )
    leaf_clusters = final_level_hierarchical_clustering(hcs)
    return modularity(graph, leaf_clusters)


def calculate_graph_modularity(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    use_root_modularity: bool = True,
) -> float:
    """Calculate modularity of the whole graph."""
    if use_root_modularity:
        return calculate_root_modularity(
            graph, max_cluster_size=max_cluster_size, random_seed=random_seed
        )
    return calculate_leaf_modularity(
        graph, max_cluster_size=max_cluster_size, random_seed=random_seed
    )


def calculate_lcc_modularity(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    use_root_modularity: bool = True,
) -> float:
    """Calculate modularity of the largest connected component of the graph."""
    lcc = cast("nx.Graph", largest_connected_component(graph))
    if use_root_modularity:
        return calculate_root_modularity(
            lcc, max_cluster_size=max_cluster_size, random_seed=random_seed
        )
    return calculate_leaf_modularity(
        lcc, max_cluster_size=max_cluster_size, random_seed=random_seed
    )


def calculate_weighted_modularity(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    min_connected_component_size: int = 10,
    use_root_modularity: bool = True,
) -> float:
    """
    Calculate weighted modularity of all connected components with size greater than min_connected_component_size.

    Modularity = sum(component_modularity * component_size) / total_nodes.
    """
    connected_components: list[set] = list(nx.connected_components(graph))
    filtered_components = [
        component
        for component in connected_components
        if len(component) > min_connected_component_size
    ]
    if len(filtered_components) == 0:
        filtered_components = [graph]

    total_nodes = sum(len(component) for component in filtered_components)
    total_modularity = 0
    for component in filtered_components:
        if len(component) > min_connected_component_size:
            subgraph = graph.subgraph(component)
            if use_root_modularity:
                modularity = calculate_root_modularity(
                    subgraph, max_cluster_size=max_cluster_size, random_seed=random_seed
                )
            else:
                modularity = calculate_leaf_modularity(
                    subgraph, max_cluster_size=max_cluster_size, random_seed=random_seed
                )
            total_modularity += modularity * len(component) / total_nodes
    return total_modularity


def calculate_modularity(
    graph: nx.Graph,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    use_root_modularity: bool = True,
    modularity_metric: ModularityMetric = ModularityMetric.WeightedComponents,
) -> float:
    """Calculate modularity of the graph based on the modularity metric type."""
    match modularity_metric:
        case ModularityMetric.Graph:
            logger.info("Calculating graph modularity")
            return calculate_graph_modularity(
                graph,
                max_cluster_size=max_cluster_size,
                random_seed=random_seed,
                use_root_modularity=use_root_modularity,
            )
        case ModularityMetric.LCC:
            logger.info("Calculating LCC modularity")
            return calculate_lcc_modularity(
                graph,
                max_cluster_size=max_cluster_size,
                random_seed=random_seed,
                use_root_modularity=use_root_modularity,
            )
        case ModularityMetric.WeightedComponents:
            logger.info("Calculating weighted-components modularity")
            return calculate_weighted_modularity(
                graph,
                max_cluster_size=max_cluster_size,
                random_seed=random_seed,
                use_root_modularity=use_root_modularity,
            )


def calculate_pmi_edge_weights(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    node_name_col: str = "title",
    node_freq_col: str = "frequency",
    edge_weight_col: str = "weight",
    edge_source_col: str = "source",
    edge_target_col: str = "target",
) -> pd.DataFrame:
    """
    Calculate pointwise mutual information (PMI) edge weights.

    Uses a variant of PMI that accounts for bias towards low-frequency events.
    pmi(x,y) = p(x,y) * log2(p(x,y)/ (p(x)*p(y))
    p(x,y) = edge_weight(x,y) / total_edge_weights
    p(x) = freq_occurrence(x) / total_freq_occurrences.

    """
    copied_nodes_df = nodes_df[[node_name_col, node_freq_col]]

    total_edge_weights = edges_df[edge_weight_col].sum()
    total_freq_occurrences = nodes_df[node_freq_col].sum()
    copied_nodes_df["prop_occurrence"] = (
        copied_nodes_df[node_freq_col] / total_freq_occurrences
    )
    copied_nodes_df = copied_nodes_df.loc[:, [node_name_col, "prop_occurrence"]]

    edges_df["prop_weight"] = edges_df[edge_weight_col] / total_edge_weights
    edges_df = (
        edges_df
        .merge(
            copied_nodes_df, left_on=edge_source_col, right_on=node_name_col, how="left"
        )
        .drop(columns=[node_name_col])
        .rename(columns={"prop_occurrence": "source_prop"})
    )
    edges_df = (
        edges_df
        .merge(
            copied_nodes_df, left_on=edge_target_col, right_on=node_name_col, how="left"
        )
        .drop(columns=[node_name_col])
        .rename(columns={"prop_occurrence": "target_prop"})
    )
    edges_df[edge_weight_col] = edges_df["prop_weight"] * np.log2(
        edges_df["prop_weight"] / (edges_df["source_prop"] * edges_df["target_prop"])
    )

    return edges_df.drop(columns=["prop_weight", "source_prop", "target_prop"])


def calculate_rrf_edge_weights(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    node_name_col="title",
    node_freq_col="freq",
    edge_weight_col="weight",
    edge_source_col="source",
    edge_target_col="target",
    rrf_smoothing_factor: int = 60,
) -> pd.DataFrame:
    """Calculate reciprocal rank fusion (RRF) edge weights as a combination of PMI weight and combined freq of source and target."""
    edges_df = calculate_pmi_edge_weights(
        nodes_df,
        edges_df,
        node_name_col,
        node_freq_col,
        edge_weight_col,
        edge_source_col,
        edge_target_col,
    )

    edges_df["pmi_rank"] = edges_df[edge_weight_col].rank(method="min", ascending=False)
    edges_df["raw_weight_rank"] = edges_df[edge_weight_col].rank(
        method="min", ascending=False
    )
    edges_df[edge_weight_col] = edges_df.apply(
        lambda x: (
            (1 / (rrf_smoothing_factor + x["pmi_rank"]))
            + (1 / (rrf_smoothing_factor + x["raw_weight_rank"]))
        ),
        axis=1,
    )

    return edges_df.drop(columns=["pmi_rank", "raw_weight_rank"])


def get_upper_threshold_by_std(data: list[float] | list[int], std_trim: float) -> float:
    """Get upper threshold by standard deviation."""
    mean = np.mean(data)
    std = np.std(data)
    return cast("float", mean + std_trim * std)


def first_level_hierarchical_clustering(
    hcs: list[gn.HierarchicalCluster],
) -> dict[Any, int]:
    """first_level_hierarchical_clustering.

    Returns
    -------
    dict[Any, int]
        The initial leiden algorithm clustering results as a dictionary
        of node id to community id.
    """
    return {entry.node: entry.cluster for entry in hcs if entry.level == 0}


def final_level_hierarchical_clustering(
    hcs: list[gn.HierarchicalCluster],
) -> dict[Any, int]:
    """
    final_level_hierarchical_clustering.

    Returns
    -------
    dict[Any, int]
        The last leiden algorithm clustering results as a dictionary
        of node id to community id.
    """
    return {entry.node: entry.cluster for entry in hcs if entry.is_final_cluster}
