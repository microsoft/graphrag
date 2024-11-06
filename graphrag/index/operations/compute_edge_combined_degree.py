# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing compute_edge_combined_degree methods definition."""

import pandas as pd


def compute_edge_combined_degree(
    edge_df: pd.DataFrame,
    node_degree_df: pd.DataFrame,
    to: str,
    node_name_column: str,
    node_degree_column: str,
    edge_source_column: str,
    edge_target_column: str,
) -> pd.DataFrame:
    """Compute the combined degree for each edge in a graph."""
    if to in edge_df.columns:
        return edge_df

    def join_to_degree(df: pd.DataFrame, column: str) -> pd.DataFrame:
        degree_column = _degree_colname(column)
        result = df.merge(
            node_degree_df.rename(
                columns={node_name_column: column, node_degree_column: degree_column}
            ),
            on=column,
            how="left",
        )
        result[degree_column] = result[degree_column].fillna(0)
        return result

    output_df = join_to_degree(edge_df, edge_source_column)
    output_df = join_to_degree(output_df, edge_target_column)
    output_df[to] = (
        output_df[_degree_colname(edge_source_column)]
        + output_df[_degree_colname(edge_target_column)]
    )
    return output_df


def _degree_colname(column: str) -> str:
    return f"{column}_degree"
