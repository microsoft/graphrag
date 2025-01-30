# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Prepare text units for community reports."""

import logging

import pandas as pd

import graphrag.index.operations.summarize_communities_text.schemas.graph as gh
import graphrag.index.operations.summarize_communities_text.schemas.text_units as ts

log = logging.getLogger(__name__)


def prep_text_units(
    text_unit_df: pd.DataFrame,
    node_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate text unit degree  and concatenate text unit details.

    Returns : dataframe with columns [NODE_COMMUNITY, TEXT_UNIT_ID, ALL_DETAILS]
    """
    node_df.drop(columns=["id"], inplace=True)
    node_to_text_ids = node_df.explode(gh.NODE_TEXT_UNIT_IDS).rename(
        columns={gh.NODE_TEXT_UNIT_IDS: ts.ID}
    )
    node_to_text_ids = node_to_text_ids[
        [gh.NODE_NAME, gh.NODE_COMMUNITY, gh.NODE_DEGREE, ts.ID]
    ]
    text_unit_degrees = (
        node_to_text_ids.groupby([gh.NODE_COMMUNITY, ts.ID])
        .agg({gh.NODE_DEGREE: sum})
        .reset_index()
    )
    result_df = text_unit_df.merge(text_unit_degrees, on=ts.ID, how="left")
    result_df[ts.ALL_DETAILS] = result_df.apply(
        lambda x: {
            ts.SHORT_ID: x[ts.SHORT_ID],
            ts.TEXT: x[ts.TEXT],
            ts.ENTITY_DEGREE: x[gh.NODE_DEGREE],
        },
        axis=1,
    )
    return result_df.loc[:, [gh.NODE_COMMUNITY, ts.ID, ts.ALL_DETAILS]]
