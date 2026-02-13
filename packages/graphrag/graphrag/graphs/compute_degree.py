# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Compute node degree directly from a relationships DataFrame."""

import pandas as pd


def compute_degree(
    relationships: pd.DataFrame,
    source_column: str = "source",
    target_column: str = "target",
) -> pd.DataFrame:
    """Compute the degree of each node from an edge list DataFrame.

    Degree is the number of edges connected to a node (counting both
    source and target appearances).

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
        DataFrame with columns ["title", "degree"].
    """
    # Normalize edge direction so (A,B) and (B,A) are treated as the same
    # undirected edge, matching NetworkX Graph behavior.
    edges = relationships[[source_column, target_column]].copy()
    edges["_lo"] = edges.min(axis=1)
    edges["_hi"] = edges.max(axis=1)
    edges = edges.drop_duplicates(subset=["_lo", "_hi"])

    source_counts = edges[source_column].value_counts()
    target_counts = edges[target_column].value_counts()
    degree = source_counts.add(target_counts, fill_value=0).astype(int)
    return pd.DataFrame({"title": degree.index, "degree": degree.to_numpy()})
