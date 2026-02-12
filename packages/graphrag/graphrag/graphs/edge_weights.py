# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Edge weight calculation utilities (PMI, RRF)."""

import numpy as np
import pandas as pd


def calculate_pmi_edge_weights(
    nodes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    node_name_col: str = "title",
    node_freq_col: str = "frequency",
    edge_weight_col: str = "weight",
    edge_source_col: str = "source",
    edge_target_col: str = "target",
) -> pd.DataFrame:
    """Calculate pointwise mutual information (PMI) edge weights.

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
            copied_nodes_df,
            left_on=edge_source_col,
            right_on=node_name_col,
            how="left",
        )
        .drop(columns=[node_name_col])
        .rename(columns={"prop_occurrence": "source_prop"})
    )
    edges_df = (
        edges_df
        .merge(
            copied_nodes_df,
            left_on=edge_target_col,
            right_on=node_name_col,
            how="left",
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
    node_name_col: str = "title",
    node_freq_col: str = "freq",
    edge_weight_col: str = "weight",
    edge_source_col: str = "source",
    edge_target_col: str = "target",
    rrf_smoothing_factor: int = 60,
) -> pd.DataFrame:
    """Calculate reciprocal rank fusion (RRF) edge weights.

    Combines PMI weight and combined freq of source and target.
    """
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
