# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
from typing import cast

import pandas as pd

import graphrag.index.graph.extractors.community_reports.schemas as schemas
from graphrag.index.graph.extractors.community_reports.build_mixed_context import (
    build_mixed_context,
)
from graphrag.index.graph.extractors.community_reports.sort_context import sort_context
from graphrag.index.graph.extractors.community_reports.utils import set_context_size
from graphrag.index.utils.dataframes import (
    antijoin,
    drop_columns,
    join,
    select,
    transform_series,
    union,
    where_column_equals,
)

log = logging.getLogger(__name__)


def prep_community_report_context(
    report_df: pd.DataFrame | None,
    community_hierarchy_df: pd.DataFrame,
    local_context_df: pd.DataFrame,
    level: int | str,
    max_tokens: int,
) -> pd.DataFrame:
    """
    Prep context for each community in a given level.

    For each community:
    - Check if local context fits within the limit, if yes use local context
    - If local context exceeds the limit, iteratively replace local context with sub-community reports, starting from the biggest sub-community
    """
    if report_df is None:
        report_df = pd.DataFrame()

    level = int(level)
    level_context_df = _at_level(level, local_context_df)
    valid_context_df = _within_context(level_context_df)
    invalid_context_df = _exceeding_context(level_context_df)

    # there is no report to substitute with, so we just trim the local context of the invalid context records
    # this case should only happen at the bottom level of the community hierarchy where there are no sub-communities
    if invalid_context_df.empty:
        return valid_context_df

    if report_df.empty:
        invalid_context_df[schemas.CONTEXT_STRING] = _sort_and_trim_context(
            invalid_context_df, max_tokens
        )
        set_context_size(invalid_context_df)
        invalid_context_df.loc[:, schemas.CONTEXT_EXCEED_FLAG] = 0
        return union(valid_context_df, invalid_context_df)

    level_context_df = _antijoin_reports(level_context_df, report_df)

    # for each invalid context, we will try to substitute with sub-community reports
    # first get local context and report (if available) for each sub-community
    sub_context_df = _get_subcontext_df(level + 1, report_df, local_context_df)
    community_df = _get_community_df(
        level, invalid_context_df, sub_context_df, community_hierarchy_df, max_tokens
    )

    # handle any remaining invalid records that can't be subsituted with sub-community reports
    # this should be rare, but if it happens, we will just trim the local context to fit the limit
    remaining_df = _antijoin_reports(invalid_context_df, community_df)
    remaining_df[schemas.CONTEXT_STRING] = _sort_and_trim_context(
        remaining_df, max_tokens
    )

    result = union(valid_context_df, community_df, remaining_df)
    set_context_size(result)
    result[schemas.CONTEXT_EXCEED_FLAG] = 0
    return result


def _drop_community_level(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the community level column from the dataframe."""
    return drop_columns(df, schemas.COMMUNITY_LEVEL)


def _at_level(level: int, df: pd.DataFrame) -> pd.DataFrame:
    """Return records at the given level."""
    return where_column_equals(df, schemas.COMMUNITY_LEVEL, level)


def _exceeding_context(df: pd.DataFrame) -> pd.DataFrame:
    """Return records where the context exceeds the limit."""
    return where_column_equals(df, schemas.CONTEXT_EXCEED_FLAG, 1)


def _within_context(df: pd.DataFrame) -> pd.DataFrame:
    """Return records where the context is within the limit."""
    return where_column_equals(df, schemas.CONTEXT_EXCEED_FLAG, 0)


def _antijoin_reports(df: pd.DataFrame, reports: pd.DataFrame) -> pd.DataFrame:
    """Return records in df that are not in reports."""
    return antijoin(df, reports, schemas.NODE_COMMUNITY)


def _sort_and_trim_context(df: pd.DataFrame, max_tokens: int) -> pd.Series:
    """Sort and trim context to fit the limit."""
    series = cast(pd.Series, df[schemas.ALL_CONTEXT])
    return transform_series(series, lambda x: sort_context(x, max_tokens=max_tokens))


def _build_mixed_context(df: pd.DataFrame, max_tokens: int) -> pd.Series:
    """Sort and trim context to fit the limit."""
    series = cast(pd.Series, df[schemas.ALL_CONTEXT])
    return transform_series(
        series, lambda x: build_mixed_context(x, max_tokens=max_tokens)
    )


def _get_subcontext_df(
    level: int, report_df: pd.DataFrame, local_context_df: pd.DataFrame
) -> pd.DataFrame:
    """Get sub-community context for each community."""
    sub_report_df = _drop_community_level(_at_level(level, report_df))
    sub_context_df = _at_level(level, local_context_df)
    sub_context_df = join(sub_context_df, sub_report_df, schemas.NODE_COMMUNITY)
    sub_context_df.rename(
        columns={schemas.NODE_COMMUNITY: schemas.SUB_COMMUNITY}, inplace=True
    )
    return sub_context_df


def _get_community_df(
    level: int,
    invalid_context_df: pd.DataFrame,
    sub_context_df: pd.DataFrame,
    community_hierarchy_df: pd.DataFrame,
    max_tokens: int,
) -> pd.DataFrame:
    """Get community context for each community."""
    # collect all sub communities' contexts for each community
    community_df = _drop_community_level(_at_level(level, community_hierarchy_df))
    invalid_community_ids = select(invalid_context_df, schemas.NODE_COMMUNITY)
    subcontext_selection = select(
        sub_context_df,
        schemas.SUB_COMMUNITY,
        schemas.FULL_CONTENT,
        schemas.ALL_CONTEXT,
        schemas.CONTEXT_SIZE,
    )

    invalid_communities = join(
        community_df, invalid_community_ids, schemas.NODE_COMMUNITY, "inner"
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
        community_df.groupby(schemas.NODE_COMMUNITY)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )
    community_df[schemas.CONTEXT_STRING] = _build_mixed_context(
        community_df, max_tokens
    )
    community_df[schemas.COMMUNITY_LEVEL] = level
    return community_df
