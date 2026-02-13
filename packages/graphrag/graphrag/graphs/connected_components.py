# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Find connected components and the largest connected component from an edge list DataFrame."""

import pandas as pd


def connected_components(
    relationships: pd.DataFrame,
    source_column: str = "source",
    target_column: str = "target",
) -> list[set[str]]:
    """Return all connected components as a list of node-title sets.

    Uses union-find on the deduplicated edge list.

    Parameters
    ----------
    relationships : pd.DataFrame
        Edge list with at least source and target columns.
    source_column : str
        Name of the source node column.
    target_column : str
        Name of the target node column.

    Returns
    -------
    list[set[str]]
        Each element is a set of node titles belonging to one component,
        sorted by descending component size.
    """
    edges = relationships.drop_duplicates(subset=[source_column, target_column])

    # Initialize every node as its own parent
    all_nodes = pd.concat(
        [edges[source_column], edges[target_column]], ignore_index=True
    ).unique()
    parent: dict[str, str] = {node: node for node in all_nodes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Union each edge
    for src, tgt in zip(edges[source_column], edges[target_column], strict=True):
        union(src, tgt)

    # Group by root
    groups: dict[str, set[str]] = {}
    for node in parent:
        root = find(node)
        groups.setdefault(root, set()).add(node)

    return sorted(groups.values(), key=len, reverse=True)


def largest_connected_component(
    relationships: pd.DataFrame,
    source_column: str = "source",
    target_column: str = "target",
) -> set[str]:
    """Return the node titles belonging to the largest connected component.

    Parameters
    ----------
    relationships : pd.DataFrame
        Edge list with at least source and target columns.
    source_column : str
        Name of the source node column.
    target_column : str
        Name of the target node column.

    Returns
    -------
    set[str]
        The set of node titles in the largest connected component.
    """
    components = connected_components(
        relationships,
        source_column=source_column,
        target_column=target_column,
    )
    if not components:
        return set()
    return components[0]
