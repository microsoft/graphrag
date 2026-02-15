# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Hierarchical Leiden clustering on edge lists."""

from typing import Any

import graspologic_native as gn


def hierarchical_leiden(
    edges: list[tuple[str, str, float]],
    max_cluster_size: int = 10,
    random_seed: int | None = 0xDEADBEEF,
) -> list[gn.HierarchicalCluster]:
    """Run hierarchical leiden on an edge list."""
    return gn.hierarchical_leiden(
        edges=edges,
        max_cluster_size=max_cluster_size,
        seed=random_seed,
        starting_communities=None,
        resolution=1.0,
        randomness=0.001,
        use_modularity=True,
        iterations=1,
    )


def first_level_hierarchical_clustering(
    hcs: list[gn.HierarchicalCluster],
) -> dict[Any, int]:
    """Return the initial leiden clustering as a dict of node id to community id.

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
    """Return the final leiden clustering as a dict of node id to community id.

    Returns
    -------
    dict[Any, int]
        The last leiden algorithm clustering results as a dictionary
        of node id to community id.
    """
    return {entry.node: entry.cluster for entry in hcs if entry.is_final_cluster}
