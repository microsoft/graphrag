# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Compute graph modularity directly from an edge list DataFrame."""

import logging
import math
from collections import defaultdict

import pandas as pd

from graphrag.config.enums import ModularityMetric
from graphrag.graphs.connected_components import (
    connected_components,
    largest_connected_component,
)
from graphrag.graphs.hierarchical_leiden import (
    final_level_hierarchical_clustering,
    first_level_hierarchical_clustering,
    hierarchical_leiden,
)

logger = logging.getLogger(__name__)


def _df_to_edge_list(
    edges: pd.DataFrame,
    source_column: str = "source",
    target_column: str = "target",
    weight_column: str = "weight",
) -> list[tuple[str, str, float]]:
    """Convert a relationships DataFrame to a sorted edge list.

    Normalizes direction and deduplicates so each undirected edge appears
    once, keeping the last occurrence's weight (matching NX behavior).
    """
    df = edges[[source_column, target_column, weight_column]].copy()
    lo = df[[source_column, target_column]].min(axis=1)
    hi = df[[source_column, target_column]].max(axis=1)
    df = df.assign(**{source_column: lo, target_column: hi})
    df = df.drop_duplicates(subset=[source_column, target_column], keep="last")
    return sorted(
        (str(row[source_column]), str(row[target_column]), float(row[weight_column]))
        for _, row in df.iterrows()
    )


def modularity(
    edges: pd.DataFrame,
    partitions: dict[str, int],
    source_column: str = "source",
    target_column: str = "target",
    weight_column: str = "weight",
    resolution: float = 1.0,
) -> float:
    """Calculate modularity of a graph given community assignments.

    Parameters
    ----------
    edges : pd.DataFrame
        Edge list with at least source, target, and weight columns.
    partitions : dict[str, int]
        Mapping from node title to community id.
    source_column : str
        Name of the source node column.
    target_column : str
        Name of the target node column.
    weight_column : str
        Name of the edge weight column.
    resolution : float
        Resolution parameter for modularity calculation.

    Returns
    -------
    float
        The modularity score.
    """
    components = _modularity_components(
        edges, partitions, source_column, target_column, weight_column, resolution
    )
    return sum(components.values())


def _modularity_component(
    intra_community_degree: float,
    total_community_degree: float,
    network_degree_sum: float,
    resolution: float,
) -> float:
    """Compute the modularity contribution of a single community."""
    community_degree_ratio = math.pow(total_community_degree, 2.0) / (
        2.0 * network_degree_sum
    )
    return (intra_community_degree - resolution * community_degree_ratio) / (
        2.0 * network_degree_sum
    )


def _modularity_components(
    edges: pd.DataFrame,
    partitions: dict[str, int],
    source_column: str = "source",
    target_column: str = "target",
    weight_column: str = "weight",
    resolution: float = 1.0,
) -> dict[int, float]:
    """Calculate per-community modularity components from an edge list.

    Edges are treated as undirected: direction is normalized and duplicates
    are removed (keeping the last occurrence's weight, matching NX behavior).
    """
    # Normalize direction and deduplicate so each undirected edge is counted once
    df = edges[[source_column, target_column, weight_column]].copy()
    lo = df[[source_column, target_column]].min(axis=1)
    hi = df[[source_column, target_column]].max(axis=1)
    df = df.assign(**{source_column: lo, target_column: hi})
    df = df.drop_duplicates(subset=[source_column, target_column], keep="last")

    total_edge_weight = 0.0
    communities = set(partitions.values())

    degree_sums_within: dict[int, float] = defaultdict(float)
    degree_sums_for: dict[int, float] = defaultdict(float)

    for _, row in df.iterrows():
        src = str(row[source_column])
        tgt = str(row[target_column])
        weight = float(row[weight_column])

        src_comm = partitions[src]
        tgt_comm = partitions[tgt]

        if src_comm == tgt_comm:
            if src == tgt:
                degree_sums_within[src_comm] += weight
            else:
                degree_sums_within[src_comm] += weight * 2.0

        degree_sums_for[src_comm] += weight
        degree_sums_for[tgt_comm] += weight
        total_edge_weight += weight

    if total_edge_weight == 0.0:
        return dict.fromkeys(communities, 0.0)

    return {
        comm: _modularity_component(
            degree_sums_within[comm],
            degree_sums_for[comm],
            total_edge_weight,
            resolution,
        )
        for comm in communities
    }


def calculate_root_modularity(
    edges: pd.DataFrame,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
) -> float:
    """Calculate modularity of the graph's root clusters."""
    edge_list = _df_to_edge_list(edges)
    hcs = hierarchical_leiden(
        edge_list,
        max_cluster_size=max_cluster_size,
        random_seed=random_seed,
    )
    root_clusters = first_level_hierarchical_clustering(hcs)
    return modularity(edges, root_clusters)


def calculate_leaf_modularity(
    edges: pd.DataFrame,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
) -> float:
    """Calculate modularity of the graph's leaf clusters."""
    edge_list = _df_to_edge_list(edges)
    hcs = hierarchical_leiden(
        edge_list,
        max_cluster_size=max_cluster_size,
        random_seed=random_seed,
    )
    leaf_clusters = final_level_hierarchical_clustering(hcs)
    return modularity(edges, leaf_clusters)


def calculate_graph_modularity(
    edges: pd.DataFrame,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    use_root_modularity: bool = True,
) -> float:
    """Calculate modularity of the whole graph."""
    if use_root_modularity:
        return calculate_root_modularity(
            edges, max_cluster_size=max_cluster_size, random_seed=random_seed
        )
    return calculate_leaf_modularity(
        edges, max_cluster_size=max_cluster_size, random_seed=random_seed
    )


def calculate_lcc_modularity(
    edges: pd.DataFrame,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    use_root_modularity: bool = True,
) -> float:
    """Calculate modularity of the largest connected component of the graph."""
    lcc_nodes = largest_connected_component(edges)
    lcc_edges = edges[edges["source"].isin(lcc_nodes) & edges["target"].isin(lcc_nodes)]
    if use_root_modularity:
        return calculate_root_modularity(
            lcc_edges, max_cluster_size=max_cluster_size, random_seed=random_seed
        )
    return calculate_leaf_modularity(
        lcc_edges, max_cluster_size=max_cluster_size, random_seed=random_seed
    )


def calculate_weighted_modularity(
    edges: pd.DataFrame,
    max_cluster_size: int = 10,
    random_seed: int = 0xDEADBEEF,
    min_connected_component_size: int = 10,
    use_root_modularity: bool = True,
) -> float:
    """Calculate weighted modularity of components larger than *min_connected_component_size*.

    Modularity = sum(component_modularity * component_size) / total_nodes.
    """
    components = connected_components(edges)
    filtered = [c for c in components if len(c) > min_connected_component_size]
    if len(filtered) == 0:
        # Fall back to the whole graph
        filtered = [set(edges["source"].unique()).union(set(edges["target"].unique()))]

    total_nodes = sum(len(c) for c in filtered)
    total_modularity = 0.0
    for component in filtered:
        if len(component) > min_connected_component_size:
            sub_edges = edges[
                edges["source"].isin(component) & edges["target"].isin(component)
            ]
            if use_root_modularity:
                mod = calculate_root_modularity(
                    sub_edges,
                    max_cluster_size=max_cluster_size,
                    random_seed=random_seed,
                )
            else:
                mod = calculate_leaf_modularity(
                    sub_edges,
                    max_cluster_size=max_cluster_size,
                    random_seed=random_seed,
                )
            total_modularity += mod * len(component) / total_nodes
    return total_modularity


def calculate_modularity(
    edges: pd.DataFrame,
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
                edges,
                max_cluster_size=max_cluster_size,
                random_seed=random_seed,
                use_root_modularity=use_root_modularity,
            )
        case ModularityMetric.LCC:
            logger.info("Calculating LCC modularity")
            return calculate_lcc_modularity(
                edges,
                max_cluster_size=max_cluster_size,
                random_seed=random_seed,
                use_root_modularity=use_root_modularity,
            )
        case ModularityMetric.WeightedComponents:
            logger.info("Calculating weighted-components modularity")
            return calculate_weighted_modularity(
                edges,
                max_cluster_size=max_cluster_size,
                random_seed=random_seed,
                use_root_modularity=use_root_modularity,
            )
