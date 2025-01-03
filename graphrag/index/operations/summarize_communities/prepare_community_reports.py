# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging

import pandas as pd

import graphrag.index.operations.summarize_communities.community_reports_extractor.schemas as schemas
from graphrag.callbacks.verb_callbacks import VerbCallbacks
from graphrag.index.operations.summarize_communities.community_reports_extractor.sort_context import (
    parallel_sort_context_batch,
)
from graphrag.index.operations.summarize_communities.community_reports_extractor.utils import (
    get_levels,
)
from graphrag.logger.progress import progress_iterable

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

        communities_at_level_df.loc[:, schemas.COMMUNITY_LEVEL] = level
        dfs.append(communities_at_level_df)

    # build initial local context for all communities
    return pd.concat(dfs)


def _prepare_reports_at_level(
    node_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    claim_df: pd.DataFrame | None,
    level: int,
    max_tokens: int = 16_000,
) -> pd.DataFrame:
    """Prepare reports at a given level."""
    # Filter and prepare node details
    level_node_df = node_df[node_df[schemas.NODE_LEVEL] == level]
    log.info("Number of nodes at level=%s => %s", level, len(level_node_df))
    nodes_set = set(level_node_df[schemas.NODE_NAME])

    # Filter and prepare edge details
    level_edge_df = edge_df[
        edge_df.loc[:, schemas.EDGE_SOURCE].isin(nodes_set)
        & edge_df.loc[:, schemas.EDGE_TARGET].isin(nodes_set)
    ]
    level_edge_df.loc[:, schemas.EDGE_DETAILS] = level_edge_df.loc[
        :,
        [
            schemas.EDGE_ID,
            schemas.EDGE_SOURCE,
            schemas.EDGE_TARGET,
            schemas.EDGE_DESCRIPTION,
            schemas.EDGE_DEGREE,
        ],
    ].to_dict(orient="records")

    level_claim_df = pd.DataFrame()
    if claim_df is not None:
        level_claim_df = claim_df[
            claim_df.loc[:, schemas.CLAIM_SUBJECT].isin(nodes_set)
        ]

    # Merge node and edge details
    # Group edge details by node and aggregate into lists
    source_edges = (
        level_edge_df.groupby(schemas.EDGE_SOURCE)
        .agg({schemas.EDGE_DETAILS: "first"})
        .reset_index()
        .rename(columns={schemas.EDGE_SOURCE: schemas.NODE_NAME})
    )

    target_edges = (
        level_edge_df.groupby(schemas.EDGE_TARGET)
        .agg({schemas.EDGE_DETAILS: "first"})
        .reset_index()
        .rename(columns={schemas.EDGE_TARGET: schemas.NODE_NAME})
    )

    # Merge aggregated edges into the node DataFrame
    merged_node_df = level_node_df.merge(
        source_edges, on=schemas.NODE_NAME, how="left"
    ).merge(target_edges, on=schemas.NODE_NAME, how="left")

    # Combine source and target edge details into a single column
    merged_node_df.loc[:, schemas.EDGE_DETAILS] = merged_node_df.loc[
        :, f"{schemas.EDGE_DETAILS}_x"
    ].combine_first(merged_node_df.loc[:, f"{schemas.EDGE_DETAILS}_y"])

    # Drop intermediate columns
    merged_node_df.drop(
        columns=[f"{schemas.EDGE_DETAILS}_x", f"{schemas.EDGE_DETAILS}_y"], inplace=True
    )

    # Aggregate node and edge details
    merged_node_df = (
        merged_node_df.groupby([
            schemas.NODE_NAME,
            schemas.NODE_COMMUNITY,
            schemas.NODE_LEVEL,
            schemas.NODE_DEGREE,
        ])
        .agg({
            schemas.NODE_DETAILS: "first",
            schemas.EDGE_DETAILS: lambda x: list(x.dropna()),
        })
        .reset_index()
    )

    # Add ALL_CONTEXT column
    # Ensure schemas.CLAIM_DETAILS exists with the correct length
    # Merge claim details if available
    if claim_df is not None:
        merged_node_df = merged_node_df.merge(
            level_claim_df.loc[
                :, [schemas.CLAIM_SUBJECT, schemas.CLAIM_DETAILS]
            ].rename(columns={schemas.CLAIM_SUBJECT: schemas.NODE_NAME}),
            on=schemas.NODE_NAME,
            how="left",
        )

    # Create the ALL_CONTEXT column
    merged_node_df[schemas.ALL_CONTEXT] = (
        merged_node_df.loc[
            :,
            [
                schemas.NODE_NAME,
                schemas.NODE_DEGREE,
                schemas.NODE_DETAILS,
                schemas.EDGE_DETAILS,
            ],
        ]
        .assign(
            **{schemas.CLAIM_DETAILS: merged_node_df[schemas.CLAIM_DETAILS]}
            if claim_df is not None
            else {}
        )
        .to_dict(orient="records")
    )

    # group all node details by community
    community_df = (
        merged_node_df.groupby(schemas.NODE_COMMUNITY)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )

    # Generate community-level context strings using vectorized batch processing
    return parallel_sort_context_batch(
        community_df,
        max_tokens=max_tokens,
    )
