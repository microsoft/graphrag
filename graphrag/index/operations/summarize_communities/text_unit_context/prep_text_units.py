# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Prepare text units for community reports."""

import logging

import pandas as pd

import graphrag.data_model.schemas as schemas

log = logging.getLogger(__name__)


def prep_text_units(
    text_unit_df: pd.DataFrame,
    node_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate text unit degree  and concatenate text unit details.

    Returns : dataframe with columns [COMMUNITY_ID, TEXT_UNIT_ID, ALL_DETAILS]
    """
    node_df.drop(columns=["id"], inplace=True)
    node_to_text_ids = node_df.explode(schemas.TEXT_UNIT_IDS).rename(
        columns={schemas.TEXT_UNIT_IDS: schemas.ID}
    )
    node_to_text_ids = node_to_text_ids[
        [schemas.TITLE, schemas.COMMUNITY_ID, schemas.NODE_DEGREE, schemas.ID]
    ]
    text_unit_degrees = (
        node_to_text_ids.groupby([schemas.COMMUNITY_ID, schemas.ID])
        .agg({schemas.NODE_DEGREE: "sum"})
        .reset_index()
    )
    result_df = text_unit_df.merge(text_unit_degrees, on=schemas.ID, how="left")
    result_df[schemas.ALL_DETAILS] = result_df.apply(
        lambda x: {
            schemas.SHORT_ID: x[schemas.SHORT_ID],
            schemas.TEXT: x[schemas.TEXT],
            schemas.ENTITY_DEGREE: x[schemas.NODE_DEGREE],
        },
        axis=1,
    )
    return result_df.loc[:, [schemas.COMMUNITY_ID, schemas.ID, schemas.ALL_DETAILS]]
