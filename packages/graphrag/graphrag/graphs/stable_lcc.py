# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Produce a stable largest connected component from a relationships DataFrame.

"Stable" means the same input edge list always produces the same output,
regardless of the original row order.  This is achieved by:

1. Filtering to the largest connected component.
2. Sorting edges so the lesser node is always the source.
3. Sorting edges alphabetically for deterministic row order.

Node names are preserved verbatim.  Downstream steps (e.g. create_communities)
match the resulting cluster labels against the original entity titles with an
exact, case-sensitive lookup, so any mutation of node names here would silently
drop entities whose titles are not already normalized (see issue #2427).
"""

import pandas as pd

from graphrag.graphs.connected_components import largest_connected_component


def stable_lcc(
    relationships: pd.DataFrame,
    source_column: str = "source",
    target_column: str = "target",
) -> pd.DataFrame:
    """Return the relationships DataFrame filtered to a stable largest connected component.

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
    pd.DataFrame
        A copy of the input filtered to the LCC with deterministic edge
        ordering.  Node names are preserved verbatim.
    """
    if relationships.empty:
        return relationships.copy()

    edges = relationships.copy()

    # 1. Filter to the largest connected component
    lcc_nodes = largest_connected_component(
        edges, source_column=source_column, target_column=target_column
    )
    edges = edges[
        edges[source_column].isin(lcc_nodes) & edges[target_column].isin(lcc_nodes)
    ]

    # 2. Stabilize edge direction: lesser node always first
    swapped = edges[source_column] > edges[target_column]
    edges.loc[swapped, [source_column, target_column]] = edges.loc[
        swapped, [target_column, source_column]
    ].to_numpy()

    # 3. Deduplicate edges that were reversed pairs in the original data
    edges = edges.drop_duplicates(subset=[source_column, target_column])

    # 4. Sort for deterministic order
    return edges.sort_values([source_column, target_column]).reset_index(drop=True)
