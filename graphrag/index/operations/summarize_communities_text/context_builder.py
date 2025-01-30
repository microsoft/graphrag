# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing prep_community_reports_data method definition."""

import logging
from typing import cast

import pandas as pd

import graphrag.index.operations.summarize_communities_text.schemas.communities as cs
import graphrag.index.operations.summarize_communities_text.schemas.graph as gh
import graphrag.index.operations.summarize_communities_text.schemas.text_units as ts
from graphrag.index.operations.summarize_communities_text.prep_text_units import (
    prep_text_units,
)
from graphrag.index.operations.summarize_communities_text.sort_context import (
    sort_context,
)
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


def prep_local_context(
    community_membership_df: pd.DataFrame,
    text_units_df: pd.DataFrame,
    node_df: pd.DataFrame,
    max_tokens: int = 16000,
) -> pd.DataFrame:
    """
    Prep context data for community report generation using text unit data.

    Community membership has columns [COMMUNITY_ID, COMMUNITY_LEVEL, ENTITY_IDS, RELATIONSHIP_IDS, TEXT_UNIT_IDS]
    """
    # get text unit details, include short_id, text, and entity degree (sum of degrees of the text unit's nodes that belong to a community)
    prepped_text_units_df = prep_text_units(text_units_df, node_df)
    prepped_text_units_df = prepped_text_units_df.rename(
        columns={ts.ID: cs.TEXT_UNIT_IDS, gh.NODE_COMMUNITY: cs.COMMUNITY_ID}
    )

    # merge text unit details with community membership
    context_df = community_membership_df.loc[
        :, [cs.COMMUNITY_ID, cs.COMMUNITY_LEVEL, cs.TEXT_UNIT_IDS]
    ]
    context_df = context_df.explode(cs.TEXT_UNIT_IDS)
    context_df = context_df.merge(
        prepped_text_units_df, on=[cs.TEXT_UNIT_IDS, cs.COMMUNITY_ID], how="left"
    )

    context_df[cs.ALL_CONTEXT] = context_df.apply(
        lambda x: {
            "id": x[ts.ALL_DETAILS][ts.SHORT_ID],
            "text": x[ts.ALL_DETAILS][ts.TEXT],
            "entity_degree": x[ts.ALL_DETAILS][ts.ENTITY_DEGREE],
        },
        axis=1,
    )

    context_df = (
        context_df.groupby([cs.COMMUNITY_ID, cs.COMMUNITY_LEVEL])
        .agg({cs.ALL_CONTEXT: list})
        .reset_index()
    )
    context_df[cs.CONTEXT_STRING] = context_df[cs.ALL_CONTEXT].apply(
        lambda x: sort_context(x)
    )
    context_df[cs.CONTEXT_SIZE] = context_df[cs.CONTEXT_STRING].apply(
        lambda x: num_tokens(x)
    )
    context_df[cs.CONTEXT_EXCEED_FLAG] = context_df[cs.CONTEXT_SIZE].apply(
        lambda x: x > max_tokens
    )

    return context_df


def prep_community_report_context(
    report_df: pd.DataFrame | None,
    community_hierarchy_df: pd.DataFrame,
    local_context_df: pd.DataFrame,
    level: int,
    max_tokens: int = 16000,
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
            local_context_df[cs.COMMUNITY_LEVEL] == level
        ]
        valid_context_df = cast(
            "pd.DataFrame",
            level_context_df[level_context_df[cs.CONTEXT_EXCEED_FLAG] == 0],
        )
        invalid_context_df = cast(
            "pd.DataFrame",
            level_context_df[level_context_df[cs.CONTEXT_EXCEED_FLAG] == 1],
        )
        if invalid_context_df.empty:
            return valid_context_df

        invalid_context_df[cs.CONTEXT_STRING] = invalid_context_df[
            cs.ALL_CONTEXT
        ].apply(lambda x: sort_context(x, max_tokens=max_tokens))
        invalid_context_df[cs.CONTEXT_SIZE] = invalid_context_df[
            cs.CONTEXT_STRING
        ].apply(lambda x: num_tokens(x))
        invalid_context_df[cs.CONTEXT_EXCEED_FLAG] = 0

        return pd.concat([valid_context_df, invalid_context_df])

    level_context_df = local_context_df[local_context_df[cs.COMMUNITY_LEVEL] == level]

    # exclude those that already have reports
    level_context_df = level_context_df.merge(
        report_df[[cs.COMMUNITY_ID]],
        on=cs.COMMUNITY_ID,
        how="outer",
        indicator=True,
    )
    level_context_df = level_context_df[level_context_df["_merge"] == "left_only"].drop(
        "_merge", axis=1
    )
    valid_context_df = cast(
        "pd.DataFrame", level_context_df[level_context_df[cs.CONTEXT_EXCEED_FLAG] == 0]
    )
    invalid_context_df = cast(
        "pd.DataFrame", level_context_df[level_context_df[cs.CONTEXT_EXCEED_FLAG] == 1]
    )

    if invalid_context_df.empty:
        return valid_context_df

    # for each invalid context, we will try to substitute with sub-community reports
    # first get local context and report (if available) for each sub-community
    sub_report_df = report_df[report_df[cs.COMMUNITY_LEVEL] == level + 1].drop(
        [cs.COMMUNITY_LEVEL], axis=1
    )
    sub_context_df = local_context_df[local_context_df[cs.COMMUNITY_LEVEL] == level + 1]
    sub_context_df = sub_context_df.merge(sub_report_df, on=cs.COMMUNITY_ID, how="left")
    sub_context_df.rename(columns={cs.COMMUNITY_ID: cs.SUB_COMMUNITY_ID}, inplace=True)

    # collect all sub communities' contexts for each community
    community_df = community_hierarchy_df[
        community_hierarchy_df[cs.COMMUNITY_LEVEL] == level
    ].drop([cs.COMMUNITY_LEVEL], axis=1)
    community_df = community_df.merge(
        invalid_context_df[[cs.COMMUNITY_ID]], on=cs.COMMUNITY_ID, how="inner"
    )
    community_df = community_df.merge(
        sub_context_df[
            [cs.SUB_COMMUNITY_ID, cs.FULL_CONTENT, cs.ALL_CONTEXT, cs.CONTEXT_SIZE]
        ],
        on=cs.SUB_COMMUNITY_ID,
        how="left",
    )
    community_df[cs.ALL_CONTEXT] = community_df.apply(
        lambda x: {
            cs.SUB_COMMUNITY_ID: x[cs.SUB_COMMUNITY_ID],
            cs.ALL_CONTEXT: x[cs.ALL_CONTEXT],
            cs.FULL_CONTENT: x[cs.FULL_CONTENT],
            cs.CONTEXT_SIZE: x[cs.CONTEXT_SIZE],
        },
        axis=1,
    )
    community_df = (
        community_df.groupby(cs.COMMUNITY_ID).agg({cs.ALL_CONTEXT: list}).reset_index()
    )
    community_df[cs.CONTEXT_STRING] = community_df[cs.ALL_CONTEXT].apply(
        lambda x: _build_mixed_context(x, max_tokens)
    )
    community_df[cs.CONTEXT_SIZE] = community_df[cs.CONTEXT_STRING].apply(
        lambda x: num_tokens(x)
    )
    community_df[cs.CONTEXT_EXCEED_FLAG] = 0
    community_df[cs.COMMUNITY_LEVEL] = level

    # handle any remaining invalid records that can't be subsituted with sub-community reports
    # this should be rare, but if it happens, we will just trim the local context to fit the limit
    remaining_df = invalid_context_df.merge(
        community_df[[cs.COMMUNITY_ID]],
        on=cs.COMMUNITY_ID,
        how="outer",
        indicator=True,
    )
    remaining_df = remaining_df[remaining_df["_merge"] == "left_only"].drop(
        "_merge", axis=1
    )
    remaining_df[cs.CONTEXT_STRING] = cast(
        "pd.DataFrame", remaining_df[cs.ALL_CONTEXT]
    ).apply(lambda x: sort_context(x, max_tokens=max_tokens))
    remaining_df[cs.CONTEXT_SIZE] = cast(
        "pd.DataFrame", remaining_df[cs.CONTEXT_STRING]
    ).apply(lambda x: num_tokens(x))
    remaining_df[cs.CONTEXT_EXCEED_FLAG] = 0

    return cast(
        "pd.DataFrame", pd.concat([valid_context_df, community_df, remaining_df])
    )


def _build_mixed_context(context: list[dict], max_tokens: int = 16000) -> str:
    """
    Build parent context by concatenating all sub-communities' contexts.

    If the context exceeds the limit, we use sub-community reports instead.
    """
    sorted_context = sorted(context, key=lambda x: x[cs.CONTEXT_SIZE], reverse=True)

    # replace local context with sub-community reports, starting from the biggest sub-community
    substitute_reports = []
    final_local_contexts = []
    exceeded_limit = True
    context_string = ""

    for idx, sub_community_context in enumerate(sorted_context):
        if exceeded_limit:
            if sub_community_context[cs.FULL_CONTENT]:
                substitute_reports.append({
                    cs.COMMUNITY_ID: sub_community_context[cs.SUB_COMMUNITY_ID],
                    cs.FULL_CONTENT: sub_community_context[cs.FULL_CONTENT],
                })
            else:
                # this sub-community has no report, so we will use its local context
                final_local_contexts.extend(sub_community_context[cs.ALL_CONTEXT])
                continue

            # add local context for the remaining sub-communities
            remaining_local_context = []
            for rid in range(idx + 1, len(sorted_context)):
                remaining_local_context.extend(sorted_context[rid][cs.ALL_CONTEXT])
            new_context_string = sort_context(
                local_context=remaining_local_context + final_local_contexts,
                sub_community_reports=substitute_reports,
            )
            if num_tokens(new_context_string) <= max_tokens:
                exceeded_limit = False
                context_string = new_context_string
                break

    if exceeded_limit:
        # if all sub-community reports exceed the limit, we add reports until context is full
        substitute_reports = []
        for sub_community_context in sorted_context:
            substitute_reports.append({
                cs.COMMUNITY_ID: sub_community_context[cs.SUB_COMMUNITY_ID],
                cs.FULL_CONTENT: sub_community_context[cs.FULL_CONTENT],
            })
            new_context_string = pd.DataFrame(substitute_reports).to_csv(
                index=False, sep=","
            )
            if num_tokens(new_context_string) > max_tokens:
                break

            context_string = new_context_string

    return context_string
