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
    source_counts = relationships.drop_duplicates(
        subset=[source_column, target_column]
    )[source_column].value_counts()
    target_counts = relationships.drop_duplicates(
        subset=[source_column, target_column]
    )[target_column].value_counts()
    degree = source_counts.add(target_counts, fill_value=0).astype(int)
    return pd.DataFrame({"title": degree.index, "degree": degree.to_numpy()})
