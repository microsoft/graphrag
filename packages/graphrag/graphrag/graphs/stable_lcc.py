# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Produce a stable largest connected component from a relationships DataFrame.

"Stable" means the same input edge list always produces the same output,
regardless of the original row order.  This is achieved by:

1. Filtering to the largest connected component.
2. Normalizing node names (HTML unescape, uppercase, strip).
3. Sorting edges so the lesser node is always the source.
4. Sorting edges alphabetically for deterministic row order.
"""

import html

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
        A copy of the input filtered to the LCC with normalized node names
        and deterministic edge ordering.
    """
    if relationships.empty:
        return relationships.copy()

    # 1. Normalize node names
    edges = relationships.copy()
    edges[source_column] = edges[source_column].apply(_normalize_name)
    edges[target_column] = edges[target_column].apply(_normalize_name)

    # 2. Filter to the largest connected component
    lcc_nodes = largest_connected_component(
        edges, source_column=source_column, target_column=target_column
    )
    edges = edges[
        edges[source_column].isin(lcc_nodes) & edges[target_column].isin(lcc_nodes)
    ]

    # 3. Stabilize edge direction: lesser node always first
    swapped = edges[source_column] > edges[target_column]
    edges.loc[swapped, [source_column, target_column]] = edges.loc[
        swapped, [target_column, source_column]
    ].to_numpy()

    # 4. Deduplicate edges that were reversed pairs in the original data
    edges = edges.drop_duplicates(subset=[source_column, target_column])

    # 5. Sort for deterministic order
    return edges.sort_values([source_column, target_column]).reset_index(drop=True)


def _normalize_name(name: str) -> str:
    """Normalize a node name: HTML unescape, uppercase, strip whitespace."""
    return html.unescape(name).upper().strip()
