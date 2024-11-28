# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
import time
from typing import cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
    progress_iterable,
)

import graphrag.index.graph.extractors.community_reports.schemas as schemas
from graphrag.index.graph.extractors.community_reports import (
    get_levels,
    set_context_exceeds_flag,
    set_context_size,
)
from graphrag.index.graph.extractors.community_reports.sort_context import sort_context_batch

log = logging.getLogger(__name__)

def prepare_community_reports(
    nodes,
    edges,
    claims,
    callbacks: VerbCallbacks,
    max_tokens: int = 16_000,
):
    """Prep communities for report generation."""
    levels = get_levels(nodes, schemas.NODE_LEVEL)
    dfs = []

    for level in progress_iterable(levels, callbacks.progress, len(levels)):
        communities_at_level_df = _prepare_reports_at_level(
            nodes, edges, claims, level, max_tokens
        )
        communities_at_level_df.loc[:,schemas.COMMUNITY_LEVEL] = level
        dfs.append(communities_at_level_df)

    # build initial local context for all communities
    return pd.concat(dfs)



def _prepare_reports_at_level(
    node_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    claim_df: pd.DataFrame | None,
    level: int,
    max_tokens: int = 16_000,
    community_id_column: str = schemas.COMMUNITY_ID,
    node_id_column: str = schemas.NODE_ID,
    node_name_column: str = schemas.NODE_NAME,
    node_details_column: str = schemas.NODE_DETAILS,
    node_level_column: str = schemas.NODE_LEVEL,
    node_degree_column: str = schemas.NODE_DEGREE,
    node_community_column: str = schemas.NODE_COMMUNITY,
    edge_id_column: str = schemas.EDGE_ID,
    edge_source_column: str = schemas.EDGE_SOURCE,
    edge_target_column: str = schemas.EDGE_TARGET,
    edge_degree_column: str = schemas.EDGE_DEGREE,
    edge_details_column: str = schemas.EDGE_DETAILS,
    claim_id_column: str = schemas.CLAIM_ID,
    claim_subject_column: str = schemas.CLAIM_SUBJECT,
    claim_details_column: str = schemas.CLAIM_DETAILS,
) -> pd.DataFrame:
    """Optimized preparation of reports at a given level."""
    start_time = time.perf_counter()

    # Filter nodes to the specified level
    level_node_df = node_df[node_df[node_level_column] == level]
    log.info("Number of nodes at level=%s => %s", level, len(level_node_df))
    nodes_set = set(level_node_df[node_name_column])

    # Filter and prepare edge details
    level_edge_df = edge_df[
        edge_df[edge_source_column].isin(nodes_set) & edge_df[edge_target_column].isin(nodes_set)
    ]
    level_edge_df.loc[:, edge_details_column] = level_edge_df.loc[:, 
        [edge_id_column, edge_source_column, edge_target_column, edge_degree_column]
    ].to_dict(orient="records")

    level_claim_df = pd.DataFrame
    if claim_df is not None:
        level_claim_df = claim_df[claim_df[claim_subject_column].isin(nodes_set)]

    # Merge node and edge details
    # Group edge details by node and aggregate into lists
    source_edges = level_edge_df.groupby(edge_source_column).agg({
        edge_details_column: "first"
    }).reset_index().rename(columns={edge_source_column: node_name_column})

    target_edges = level_edge_df.groupby(edge_target_column).agg({
        edge_details_column: "first"
    }).reset_index().rename(columns={edge_target_column: node_name_column})

    # Merge aggregated edges into the node DataFrame
    merged_node_df = level_node_df.merge(
        source_edges,
        on=node_name_column,
        how="left"
    ).merge(
        target_edges,
        on=node_name_column,
        how="left"
    )
    
    # Combine source and target edge details into a single column
    merged_node_df.loc[:,edge_details_column] = merged_node_df[f"{edge_details_column}_x"].combine_first(merged_node_df[f"{edge_details_column}_y"])

    # Drop intermediate columns
    merged_node_df.drop(columns=[f"{edge_details_column}_x", f"{edge_details_column}_y"], inplace=True)

    # Aggregate node and edge details
    merged_node_df = merged_node_df.groupby([
        node_name_column, node_community_column, node_level_column, node_degree_column
    ]).agg({
        node_details_column: "first",
        edge_details_column: lambda x: list(x.dropna()),
    }).reset_index()

    # Add ALL_CONTEXT column
    # Ensure claim_details_column exists with the correct length
    # Merge claim details if available
    if claim_df is not None:
        merged_node_df = merged_node_df.merge(
            level_claim_df[[claim_subject_column, claim_details_column]]
                .rename(columns={claim_subject_column: node_name_column}),
            on=node_name_column,
            how="left"
        )

    # Create the ALL_CONTEXT column
    merged_node_df[schemas.ALL_CONTEXT] = (
        merged_node_df.loc[:, [node_name_column, node_degree_column, node_details_column, edge_details_column]]
        .assign(
            **{claim_details_column: merged_node_df[claim_details_column]}
        )
        .to_dict(orient="records")
    )

    # Generate community-level context strings using vectorized batch processing
    community_df = sort_context_batch(
        merged_node_df,
        node_id_column=node_id_column,
        node_name_column=node_name_column,
        node_details_column=node_details_column,
        edge_id_column=edge_id_column,
        edge_details_column=edge_details_column,
        edge_degree_column=edge_degree_column,
        edge_source_column=edge_source_column,
        edge_target_column=edge_target_column,
        claim_id_column=claim_id_column,
        claim_details_column=claim_details_column,
        community_id_column=node_community_column,
        max_tokens=max_tokens,
    )

    print(f"Time taken to prepare reports at level {level}: {time.perf_counter() - start_time}")

    return community_df