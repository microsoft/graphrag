# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Context builders for graphs."""

import logging
from typing import cast

import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.summarize_communities.build_mixed_context import (
    build_mixed_context,
)
from graphrag.index.operations.summarize_communities.graph_context.sort_context import (
    parallel_sort_context_batch,
    sort_context,
)
from graphrag.index.operations.summarize_communities.utils import (
    get_levels,
)
from graphrag.index.utils.dataframes import (
    antijoin,
    drop_columns,
    join,
    select,
    transform_series,
    union,
    where_column_equals,
)
from graphrag.logger.progress import progress_iterable
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


def build_local_context(
    nodes,
    edges,
    claims,
    callbacks: WorkflowCallbacks,
    max_context_tokens: int = 16_000,
):
    """Prep communities for report generation."""
    levels = get_levels(nodes, schemas.COMMUNITY_LEVEL)

    dfs = []

    for level in progress_iterable(levels, callbacks.progress, len(levels)):
        communities_at_level_df = _prepare_reports_at_level(
            nodes, edges, claims, level, max_context_tokens
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
    max_context_tokens: int = 16_000,
) -> pd.DataFrame:
    """Prepare reports at a given level."""
    # Filter and prepare node details
    level_node_df = node_df[node_df[schemas.COMMUNITY_LEVEL] == level]
    log.info("Number of nodes at level=%s => %s", level, len(level_node_df))
    nodes_set = set(level_node_df[schemas.TITLE])

    # Filter and prepare edge details
    level_edge_df = edge_df[
        edge_df.loc[:, schemas.EDGE_SOURCE].isin(nodes_set)
        & edge_df.loc[:, schemas.EDGE_TARGET].isin(nodes_set)
    ]
    level_edge_df.loc[:, schemas.EDGE_DETAILS] = level_edge_df.loc[
        :,
        [
            schemas.SHORT_ID,
            schemas.EDGE_SOURCE,
            schemas.EDGE_TARGET,
            schemas.DESCRIPTION,
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
        .rename(columns={schemas.EDGE_SOURCE: schemas.TITLE})
    )

    target_edges = (
        level_edge_df.groupby(schemas.EDGE_TARGET)
        .agg({schemas.EDGE_DETAILS: "first"})
        .reset_index()
        .rename(columns={schemas.EDGE_TARGET: schemas.TITLE})
    )

    # Merge aggregated edges into the node DataFrame
    merged_node_df = level_node_df.merge(
        source_edges, on=schemas.TITLE, how="left"
    ).merge(target_edges, on=schemas.TITLE, how="left")

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
            schemas.TITLE,
            schemas.COMMUNITY_ID,
            schemas.COMMUNITY_LEVEL,
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
            ].rename(columns={schemas.CLAIM_SUBJECT: schemas.TITLE}),
            on=schemas.TITLE,
            how="left",
        )

    # Create the ALL_CONTEXT column
    merged_node_df[schemas.ALL_CONTEXT] = (
        merged_node_df.loc[
            :,
            [
                schemas.TITLE,
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
        merged_node_df.groupby(schemas.COMMUNITY_ID)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )

    # Generate community-level context strings using vectorized batch processing
    return parallel_sort_context_batch(
        community_df,
        max_context_tokens=max_context_tokens,
    )


def build_level_context(
    report_df: pd.DataFrame | None,
    community_hierarchy_df: pd.DataFrame,
    local_context_df: pd.DataFrame,
    level: int,
    max_context_tokens: int,
) -> pd.DataFrame:
    """
    Prep context for each community in a given level.

    For each community:
    - Check if local context fits within the limit, if yes use local context
    - If local context exceeds the limit, iteratively replace local context with sub-community reports, starting from the biggest sub-community
    """
    # Filter by community level
    level_context_df = local_context_df.loc[
        local_context_df.loc[:, schemas.COMMUNITY_LEVEL] == level
    ]

    # Filter valid and invalid contexts using boolean logic
    valid_context_df = level_context_df.loc[
        ~level_context_df.loc[:, schemas.CONTEXT_EXCEED_FLAG]
    ]
    invalid_context_df = level_context_df.loc[
        level_context_df.loc[:, schemas.CONTEXT_EXCEED_FLAG]
    ]

    # there is no report to substitute with, so we just trim the local context of the invalid context records
    # this case should only happen at the bottom level of the community hierarchy where there are no sub-communities
    if invalid_context_df.empty:
        return valid_context_df

    if report_df is None or report_df.empty:
        invalid_context_df.loc[:, schemas.CONTEXT_STRING] = _sort_and_trim_context(
            invalid_context_df, max_context_tokens
        )
        invalid_context_df[schemas.CONTEXT_SIZE] = invalid_context_df.loc[
            :, schemas.CONTEXT_STRING
        ].map(num_tokens)
        invalid_context_df[schemas.CONTEXT_EXCEED_FLAG] = False
        return union(valid_context_df, invalid_context_df)

    level_context_df = _antijoin_reports(level_context_df, report_df)

    # for each invalid context, we will try to substitute with sub-community reports
    # first get local context and report (if available) for each sub-community
    sub_context_df = _get_subcontext_df(level + 1, report_df, local_context_df)
    community_df = _get_community_df(
        level,
        invalid_context_df,
        sub_context_df,
        community_hierarchy_df,
        max_context_tokens,
    )

    # handle any remaining invalid records that can't be subsituted with sub-community reports
    # this should be rare, but if it happens, we will just trim the local context to fit the limit
    remaining_df = _antijoin_reports(invalid_context_df, community_df)
    remaining_df.loc[:, schemas.CONTEXT_STRING] = _sort_and_trim_context(
        remaining_df, max_context_tokens
    )

    result = union(valid_context_df, community_df, remaining_df)
    result[schemas.CONTEXT_SIZE] = result.loc[:, schemas.CONTEXT_STRING].map(num_tokens)

    result[schemas.CONTEXT_EXCEED_FLAG] = False
    return result


def _drop_community_level(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the community level column from the dataframe."""
    return drop_columns(df, schemas.COMMUNITY_LEVEL)


def _at_level(level: int, df: pd.DataFrame) -> pd.DataFrame:
    """Return records at the given level."""
    return where_column_equals(df, schemas.COMMUNITY_LEVEL, level)


def _antijoin_reports(df: pd.DataFrame, reports: pd.DataFrame) -> pd.DataFrame:
    """Return records in df that are not in reports."""
    return antijoin(df, reports, schemas.COMMUNITY_ID)


def _sort_and_trim_context(df: pd.DataFrame, max_context_tokens: int) -> pd.Series:
    """Sort and trim context to fit the limit."""
    series = cast("pd.Series", df[schemas.ALL_CONTEXT])
    return transform_series(
        series, lambda x: sort_context(x, max_context_tokens=max_context_tokens)
    )


def _build_mixed_context(df: pd.DataFrame, max_context_tokens: int) -> pd.Series:
    """Sort and trim context to fit the limit."""
    series = cast("pd.Series", df[schemas.ALL_CONTEXT])
    return transform_series(
        series, lambda x: build_mixed_context(x, max_context_tokens=max_context_tokens)
    )


def _get_subcontext_df(
    level: int, report_df: pd.DataFrame, local_context_df: pd.DataFrame
) -> pd.DataFrame:
    """Get sub-community context for each community."""
    sub_report_df = _drop_community_level(_at_level(level, report_df))
    sub_context_df = _at_level(level, local_context_df)
    sub_context_df = join(sub_context_df, sub_report_df, schemas.COMMUNITY_ID)
    sub_context_df.rename(
        columns={schemas.COMMUNITY_ID: schemas.SUB_COMMUNITY}, inplace=True
    )
    return sub_context_df


def _get_community_df(
    level: int,
    invalid_context_df: pd.DataFrame,
    sub_context_df: pd.DataFrame,
    community_hierarchy_df: pd.DataFrame,
    max_context_tokens: int,
) -> pd.DataFrame:
    """Get community context for each community."""
    # collect all sub communities' contexts for each community
    community_df = _drop_community_level(_at_level(level, community_hierarchy_df))
    invalid_community_ids = select(invalid_context_df, schemas.COMMUNITY_ID)
    subcontext_selection = select(
        sub_context_df,
        schemas.SUB_COMMUNITY,
        schemas.FULL_CONTENT,
        schemas.ALL_CONTEXT,
        schemas.CONTEXT_SIZE,
    )

    invalid_communities = join(
        community_df, invalid_community_ids, schemas.COMMUNITY_ID, "inner"
    )
    community_df = join(
        invalid_communities, subcontext_selection, schemas.SUB_COMMUNITY
    )
    community_df[schemas.ALL_CONTEXT] = community_df.apply(
        lambda x: {
            schemas.SUB_COMMUNITY: x[schemas.SUB_COMMUNITY],
            schemas.ALL_CONTEXT: x[schemas.ALL_CONTEXT],
            schemas.FULL_CONTENT: x[schemas.FULL_CONTENT],
            schemas.CONTEXT_SIZE: x[schemas.CONTEXT_SIZE],
        },
        axis=1,
    )
    community_df = (
        community_df.groupby(schemas.COMMUNITY_ID)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )
    community_df[schemas.CONTEXT_STRING] = _build_mixed_context(
        community_df, max_context_tokens
    )
    community_df[schemas.COMMUNITY_LEVEL] = level
    return community_df
