# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Graph pruning."""

import numpy as np
import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.graphs.compute_degree import compute_degree
from graphrag.graphs.connected_components import largest_connected_component


def prune_graph(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    min_node_freq: int = 1,
    max_node_freq_std: float | None = None,
    min_node_degree: int = 1,
    max_node_degree_std: float | None = None,
    min_edge_weight_pct: float = 40,
    remove_ego_nodes: bool = False,
    lcc_only: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prune graph by removing out-of-range nodes and low-weight edges.

    Returns the pruned *entities* and *relationships* DataFrames.
    """
    # -- Compute degrees from the original edge list --------------------------
    degree_df = compute_degree(relationships)
    degree_map: dict[str, int] = dict(
        zip(degree_df["title"], degree_df["degree"], strict=True)
    )

    # Entity-only nodes (isolated, degree 0) must also be present so that
    # degree thresholds are computed over the same population as before.
    entity_titles: set[str] = set(entities["title"])
    for t in entity_titles:
        degree_map.setdefault(t, 0)

    degree_values = list(degree_map.values())
    nodes_to_remove: set[str] = set()

    # -- Ego node removal (highest degree) ------------------------------------
    if remove_ego_nodes and degree_map:
        ego_node = max(degree_map, key=lambda n: degree_map[n])
        nodes_to_remove.add(ego_node)

    # -- Degree-based removal -------------------------------------------------
    for node, deg in degree_map.items():
        if deg < min_node_degree:
            nodes_to_remove.add(node)

    if max_node_degree_std is not None and degree_values:
        upper = _get_upper_threshold_by_std(degree_values, max_node_degree_std)
        for node, deg in degree_map.items():
            if deg > upper:
                nodes_to_remove.add(node)

    # -- Apply degree removals before frequency filtering ---------------------
    # NX mutates sequentially, so frequency thresholds are computed over the
    # set of entity nodes that survived degree-based removal.
    remaining = entities[~entities["title"].isin(nodes_to_remove)]

    # -- Frequency-based removal ----------------------------------------------
    freq_col = schemas.NODE_FREQUENCY
    if freq_col in remaining.columns:
        low_freq = remaining.loc[remaining[freq_col] < min_node_freq, "title"]
        nodes_to_remove.update(low_freq)
        remaining = remaining[~remaining["title"].isin(nodes_to_remove)]

        if max_node_freq_std is not None and len(remaining) > 0:
            freq_values = remaining[freq_col].tolist()
            upper = _get_upper_threshold_by_std(freq_values, max_node_freq_std)
            high_freq = remaining.loc[remaining[freq_col] > upper, "title"]
            nodes_to_remove.update(high_freq)

    # -- Filter to surviving entity nodes -------------------------------------
    kept_titles = entity_titles - nodes_to_remove
    pruned_entities = entities[entities["title"].isin(kept_titles)]
    pruned_rels = relationships[
        relationships["source"].isin(kept_titles)
        & relationships["target"].isin(kept_titles)
    ]

    # -- Edge weight filtering ------------------------------------------------
    if (
        len(pruned_rels) > 0
        and min_edge_weight_pct > 0
        and schemas.EDGE_WEIGHT in pruned_rels.columns
    ):
        min_weight = np.percentile(
            pruned_rels[schemas.EDGE_WEIGHT].to_numpy(), min_edge_weight_pct
        )
        pruned_rels = pruned_rels[pruned_rels[schemas.EDGE_WEIGHT] >= min_weight]

    # -- LCC ------------------------------------------------------------------
    if lcc_only and len(pruned_rels) > 0:
        lcc_nodes = largest_connected_component(pruned_rels)
        pruned_entities = pruned_entities[pruned_entities["title"].isin(lcc_nodes)]
        pruned_rels = pruned_rels[
            pruned_rels["source"].isin(lcc_nodes)
            & pruned_rels["target"].isin(lcc_nodes)
        ]

    return pruned_entities.reset_index(drop=True), pruned_rels.reset_index(drop=True)


def _get_upper_threshold_by_std(
    data: list[float] | list[int], std_trim: float
) -> float:
    """Get upper threshold by standard deviation."""
    mean = np.mean(data)
    std = np.std(data)
    return mean + std_trim * std  # type: ignore
