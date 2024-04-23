# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

import logging

import pandas as pd

import graphrag.index.verbs.graph.report.schemas as schemas
from graphrag.query.llm.text_utils import num_tokens

from .sort_context import build_mixed_context, sort_context

log = logging.getLogger(__name__)


def prep_community_report_context(
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
    level = int(level)
    report_df = pd.DataFrame()

    if report_df is None or report_df.empty:
        # there is no report to substitute with, so we just trim the local context of the invalid context records
        # this case should only happen at the bottom level of the community hierarchy where there are no sub-communities
        level_context_df = local_context_df[
            local_context_df[schemas.COMMUNITY_LEVEL] == level
        ]
        valid_context_df = level_context_df[
            level_context_df[schemas.CONTEXT_EXCEED_FLAG] == 0
        ]
        invalid_context_df = level_context_df[
            level_context_df[schemas.CONTEXT_EXCEED_FLAG] == 1
        ]
        if invalid_context_df.empty:
            return valid_context_df

        invalid_context_df[schemas.CONTEXT_STRING] = invalid_context_df[
            schemas.ALL_CONTEXT
        ].apply(lambda x: sort_context(x, max_tokens=max_tokens))
        invalid_context_df[schemas.CONTEXT_SIZE] = invalid_context_df[
            schemas.CONTEXT_STRING
        ].apply(lambda x: num_tokens(x))
        invalid_context_df[schemas.CONTEXT_EXCEED_FLAG] = 0
        return pd.concat([valid_context_df, invalid_context_df])

    level_context_df = local_context_df[
        local_context_df[schemas.COMMUNITY_LEVEL] == level
    ]
    level_context_df = level_context_df[level_context_df["_merge"] == "left_only"].drop(
        "_merge", axis=1
    )
    valid_context_df = level_context_df[
        level_context_df[schemas.CONTEXT_EXCEED_FLAG] == 0
    ]
    invalid_context_df = level_context_df[
        level_context_df[schemas.CONTEXT_EXCEED_FLAG] == 1
    ]

    if invalid_context_df.empty:
        return valid_context_df

    # for each invalid context, we will try to substitute with sub-community reports
    # first get local context and report (if available) for each sub-community
    sub_report_df = report_df[report_df[schemas.COMMUNITY_LEVEL] == level + 1].drop(
        [schemas.COMMUNITY_LEVEL], axis=1
    )
    sub_context_df = local_context_df[
        local_context_df[schemas.COMMUNITY_LEVEL] == level + 1
    ]
    sub_context_df = sub_context_df.merge(
        sub_report_df, on=schemas.NODE_COMMUNITY, how="left"
    )
    sub_context_df.rename(
        columns={schemas.NODE_COMMUNITY: schemas.SUB_COMMUNITY}, inplace=True
    )

    # collect all sub communities' contexts for each community
    community_df = community_hierarchy_df[
        community_hierarchy_df[schemas.COMMUNITY_LEVEL] == level
    ].drop([schemas.COMMUNITY_LEVEL], axis=1)
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
    community_df[schemas.CONTEXT_SIZE] = community_df[schemas.CONTEXT_STRING].apply(
        lambda x: num_tokens(x)
    )
    community_df[schemas.CONTEXT_EXCEED_FLAG] = 0
    community_df[schemas.COMMUNITY_LEVEL] = level

    # handle any remaining invalid records that can't be subsituted with sub-community reports
    # this should be rare, but if it happens, we will just trim the local context to fit the limit
    remaining_df = invalid_context_df.merge(
        community_df[[schemas.NODE_COMMUNITY]],
        on=schemas.NODE_COMMUNITY,
        how="outer",
        indicator=True,
    )
    remaining_df = remaining_df[remaining_df["_merge"] == "left_only"].drop(
        "_merge", axis=1
    )
    remaining_df[schemas.CONTEXT_STRING] = remaining_df[schemas.ALL_CONTEXT].apply(
        lambda x: sort_context(x, max_tokens=max_tokens)
    )
    remaining_df[schemas.CONTEXT_SIZE] = remaining_df[schemas.CONTEXT_STRING].apply(
        lambda x: num_tokens(x)
    )
    remaining_df[schemas.CONTEXT_EXCEED_FLAG] = 0

    return pd.concat([valid_context_df, community_df, remaining_df])
