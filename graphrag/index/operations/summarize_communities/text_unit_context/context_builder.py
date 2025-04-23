# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Context builders for text units."""

import logging
from typing import cast

import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.index.operations.summarize_communities.build_mixed_context import (
    build_mixed_context,
)
from graphrag.index.operations.summarize_communities.text_unit_context.prep_text_units import (
    prep_text_units,
)
from graphrag.index.operations.summarize_communities.text_unit_context.sort_context import (
    sort_context,
)
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


def build_local_context(
    community_membership_df: pd.DataFrame,
    text_units_df: pd.DataFrame,
    node_df: pd.DataFrame,
    max_context_tokens: int = 16000,
) -> pd.DataFrame:
    """
    Prep context data for community report generation using text unit data.

    Community membership has columns [COMMUNITY_ID, COMMUNITY_LEVEL, ENTITY_IDS, RELATIONSHIP_IDS, TEXT_UNIT_IDS]
    """
    # get text unit details, include short_id, text, and entity degree (sum of degrees of the text unit's nodes that belong to a community)
    prepped_text_units_df = prep_text_units(text_units_df, node_df)
    prepped_text_units_df = prepped_text_units_df.rename(
        columns={
            schemas.ID: schemas.TEXT_UNIT_IDS,
            schemas.COMMUNITY_ID: schemas.COMMUNITY_ID,
        }
    )

    # merge text unit details with community membership
    context_df = community_membership_df.loc[
        :, [schemas.COMMUNITY_ID, schemas.COMMUNITY_LEVEL, schemas.TEXT_UNIT_IDS]
    ]
    context_df = context_df.explode(schemas.TEXT_UNIT_IDS)
    context_df = context_df.merge(
        prepped_text_units_df,
        on=[schemas.TEXT_UNIT_IDS, schemas.COMMUNITY_ID],
        how="left",
    )

    context_df[schemas.ALL_CONTEXT] = context_df.apply(
        lambda x: {
            "id": x[schemas.ALL_DETAILS][schemas.SHORT_ID],
            "text": x[schemas.ALL_DETAILS][schemas.TEXT],
            "entity_degree": x[schemas.ALL_DETAILS][schemas.ENTITY_DEGREE],
        },
        axis=1,
    )

    context_df = (
        context_df.groupby([schemas.COMMUNITY_ID, schemas.COMMUNITY_LEVEL])
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )
    context_df[schemas.CONTEXT_STRING] = context_df[schemas.ALL_CONTEXT].apply(
        lambda x: sort_context(x)
    )
    context_df[schemas.CONTEXT_SIZE] = context_df[schemas.CONTEXT_STRING].apply(
        lambda x: num_tokens(x)
    )
    context_df[schemas.CONTEXT_EXCEED_FLAG] = context_df[schemas.CONTEXT_SIZE].apply(
        lambda x: x > max_context_tokens
    )

    return context_df


def build_level_context(
    report_df: pd.DataFrame | None,
    community_hierarchy_df: pd.DataFrame,
    local_context_df: pd.DataFrame,
    level: int,
    max_context_tokens: int = 16000,
) -> pd.DataFrame:
    """
    Prep context for each community in a given level.

    For each community:
    - Check if local context fits within the limit, if yes use local context
    - If local context exceeds the limit, iteratively replace local context with sub-community reports, starting from the biggest sub-community
    """
    if report_df is None or report_df.empty:
        # there is no report to substitute with, so we just trim the local context of the invalid context records
        # this case should only happen at the bottom level of the community hierarchy where there are no sub-communities
        level_context_df = local_context_df[
            local_context_df[schemas.COMMUNITY_LEVEL] == level
        ]

        valid_context_df = cast(
            "pd.DataFrame",
            level_context_df[~level_context_df[schemas.CONTEXT_EXCEED_FLAG]],
        )
        invalid_context_df = cast(
            "pd.DataFrame",
            level_context_df[level_context_df[schemas.CONTEXT_EXCEED_FLAG]],
        )

        if invalid_context_df.empty:
            return valid_context_df

        invalid_context_df.loc[:, [schemas.CONTEXT_STRING]] = invalid_context_df[
            schemas.ALL_CONTEXT
        ].apply(lambda x: sort_context(x, max_context_tokens=max_context_tokens))
        invalid_context_df.loc[:, [schemas.CONTEXT_SIZE]] = invalid_context_df[
            schemas.CONTEXT_STRING
        ].apply(lambda x: num_tokens(x))
        invalid_context_df.loc[:, [schemas.CONTEXT_EXCEED_FLAG]] = False

        return pd.concat([valid_context_df, invalid_context_df])

    level_context_df = local_context_df[
        local_context_df[schemas.COMMUNITY_LEVEL] == level
    ]

    # exclude those that already have reports
    level_context_df = level_context_df.merge(
        report_df[[schemas.COMMUNITY_ID]],
        on=schemas.COMMUNITY_ID,
        how="outer",
        indicator=True,
    )
    level_context_df = level_context_df[level_context_df["_merge"] == "left_only"].drop(
        "_merge", axis=1
    )
    valid_context_df = cast(
        "pd.DataFrame",
        level_context_df[level_context_df[schemas.CONTEXT_EXCEED_FLAG] is False],
    )
    invalid_context_df = cast(
        "pd.DataFrame",
        level_context_df[level_context_df[schemas.CONTEXT_EXCEED_FLAG] is True],
    )

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
        sub_report_df, on=schemas.COMMUNITY_ID, how="left"
    )
    sub_context_df.rename(
        columns={schemas.COMMUNITY_ID: schemas.SUB_COMMUNITY}, inplace=True
    )

    # collect all sub communities' contexts for each community
    community_df = community_hierarchy_df[
        community_hierarchy_df[schemas.COMMUNITY_LEVEL] == level
    ].drop([schemas.COMMUNITY_LEVEL], axis=1)
    community_df = community_df.merge(
        invalid_context_df[[schemas.COMMUNITY_ID]], on=schemas.COMMUNITY_ID, how="inner"
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
        community_df.groupby(schemas.COMMUNITY_ID)
        .agg({schemas.ALL_CONTEXT: list})
        .reset_index()
    )
    community_df[schemas.CONTEXT_STRING] = community_df[schemas.ALL_CONTEXT].apply(
        lambda x: build_mixed_context(x, max_context_tokens)
    )
    community_df[schemas.CONTEXT_SIZE] = community_df[schemas.CONTEXT_STRING].apply(
        lambda x: num_tokens(x)
    )
    community_df[schemas.CONTEXT_EXCEED_FLAG] = False
    community_df[schemas.COMMUNITY_LEVEL] = level

    # handle any remaining invalid records that can't be subsituted with sub-community reports
    # this should be rare, but if it happens, we will just trim the local context to fit the limit
    remaining_df = invalid_context_df.merge(
        community_df[[schemas.COMMUNITY_ID]],
        on=schemas.COMMUNITY_ID,
        how="outer",
        indicator=True,
    )
    remaining_df = remaining_df[remaining_df["_merge"] == "left_only"].drop(
        "_merge", axis=1
    )
    remaining_df[schemas.CONTEXT_STRING] = cast(
        "pd.DataFrame", remaining_df[schemas.ALL_CONTEXT]
    ).apply(lambda x: sort_context(x, max_context_tokens=max_context_tokens))
    remaining_df[schemas.CONTEXT_SIZE] = cast(
        "pd.DataFrame", remaining_df[schemas.CONTEXT_STRING]
    ).apply(lambda x: num_tokens(x))
    remaining_df[schemas.CONTEXT_EXCEED_FLAG] = False

    return cast(
        "pd.DataFrame", pd.concat([valid_context_df, community_df, remaining_df])
    )
