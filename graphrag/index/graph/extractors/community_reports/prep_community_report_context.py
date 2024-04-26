# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
from typing import cast

import pandas as pd

import graphrag.index.graph.extractors.community_reports.schemas as schemas

from .build_mixed_context import build_mixed_context
from .sort_context import sort_context
from .utils import set_context_size

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

    def drop_community_level(df: pd.DataFrame) -> pd.DataFrame:
        return df.drop([schemas.COMMUNITY_LEVEL], axis=1)

    def at_level(level: int, df: pd.DataFrame) -> pd.DataFrame:
        return cast(pd.DataFrame, df[df[schemas.COMMUNITY_LEVEL] == level])

    def exceeding_context(df: pd.DataFrame) -> pd.DataFrame:
        return cast(pd.DataFrame, df[df[schemas.CONTEXT_EXCEED_FLAG] == 1])

    def within_context(df: pd.DataFrame) -> pd.DataFrame:
        return cast(pd.DataFrame, df[df[schemas.CONTEXT_EXCEED_FLAG] == 0])

    def sort_and_trim_context(
        df: pd.DataFrame, max_tokens: int = max_tokens
    ) -> pd.Series:
        return cast(
            pd.Series,
            df[schemas.ALL_CONTEXT].apply(
                lambda x: sort_context(x, max_tokens=max_tokens)
            ),
        )

    def drop_merge_leftover(df: pd.DataFrame) -> pd.DataFrame:
        return cast(
            pd.DataFrame, df[df["_merge"] == "left_only"].drop("_merge", axis=1)
        )

    level = int(level)
    level_context_df = at_level(level, local_context_df)
    valid_context_df = within_context(level_context_df)
    invalid_context_df = exceeding_context(level_context_df)

    # there is no report to substitute with, so we just trim the local context of the invalid context records
    # this case should only happen at the bottom level of the community hierarchy where there are no sub-communities
    if invalid_context_df.empty:
        return valid_context_df

    if report_df.empty:
        invalid_context_df[schemas.CONTEXT_STRING] = sort_and_trim_context(
            invalid_context_df
        )
        set_context_size(invalid_context_df)
        invalid_context_df[schemas.CONTEXT_EXCEED_FLAG] = 0
        return pd.concat([valid_context_df, invalid_context_df])

    level_context_df = drop_merge_leftover(level_context_df)

    # for each invalid context, we will try to substitute with sub-community reports
    # first get local context and report (if available) for each sub-community
    sub_report_df = drop_community_level(at_level(level + 1, report_df))
    sub_context_df = at_level(level + 1, local_context_df)
    sub_context_df = sub_context_df.merge(
        sub_report_df, on=schemas.NODE_COMMUNITY, how="left"
    )
    sub_context_df.rename(
        columns={schemas.NODE_COMMUNITY: schemas.SUB_COMMUNITY}, inplace=True
    )

    # collect all sub communities' contexts for each community
    community_df = drop_community_level(at_level(level, community_hierarchy_df))
    community_df = community_df.merge(
        invalid_context_df[[schemas.NODE_COMMUNITY]],
        on=schemas.NODE_COMMUNITY,
        how="inner",
    )
    community_df = community_df.merge(
        sub_context_df[
            [
                schemas.SUB_COMMUNITY,
                schemas.FULL_CONTENT,
                schemas.ALL_CONTEXT,
                schemas.CONTEXT_SIZE,
            ]
        ],
        on=schemas.SUB_COMMUNITY,
        how="left",
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
    community_df[schemas.CONTEXT_STRING] = community_df[schemas.ALL_CONTEXT].apply(
        lambda x: build_mixed_context(x, max_tokens)
    )
    community_df[schemas.COMMUNITY_LEVEL] = level

    # handle any remaining invalid records that can't be subsituted with sub-community reports
    # this should be rare, but if it happens, we will just trim the local context to fit the limit
    remaining_df = invalid_context_df.merge(
        community_df[[schemas.NODE_COMMUNITY]],
        on=schemas.NODE_COMMUNITY,
        how="outer",
        indicator=True,
    )
    remaining_df = drop_merge_leftover(remaining_df)
    remaining_df[schemas.CONTEXT_STRING] = sort_and_trim_context(remaining_df)

    result = pd.concat([valid_context_df, community_df, remaining_df])
    set_context_size(result)
    result[schemas.CONTEXT_EXCEED_FLAG] = 0
    return result
