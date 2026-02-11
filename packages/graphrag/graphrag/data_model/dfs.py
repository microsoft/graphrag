# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing dataframe processing utilities."""

from typing import Any

import pandas as pd

from graphrag.data_model.schemas import (
    COMMUNITY_CHILDREN,
    COMMUNITY_ID,
    COMMUNITY_LEVEL,
    COVARIATE_IDS,
    EDGE_DEGREE,
    EDGE_WEIGHT,
    ENTITY_IDS,
    FINDINGS,
    N_TOKENS,
    NODE_DEGREE,
    NODE_FREQUENCY,
    PERIOD,
    RATING,
    RELATIONSHIP_IDS,
    SHORT_ID,
    SIZE,
    TEXT_UNIT_IDS,
)


def _split_list_column(value: Any) -> list[Any]:
    """Split a column containing a list string into an actual list."""
    if isinstance(value, str):
        return [item.strip("[] '") for item in value.split(",")] if value else []
    return value


def entities_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the entities dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)
    if NODE_FREQUENCY in df.columns:
        df[NODE_FREQUENCY] = df[NODE_FREQUENCY].astype(int)
    if NODE_DEGREE in df.columns:
        df[NODE_DEGREE] = df[NODE_DEGREE].astype(int)

    return df


def relationships_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the relationships dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    if EDGE_WEIGHT in df.columns:
        df[EDGE_WEIGHT] = df[EDGE_WEIGHT].astype(float)
    if EDGE_DEGREE in df.columns:
        df[EDGE_DEGREE] = df[EDGE_DEGREE].astype(int)
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)

    return df


def communities_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the communities dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    df[COMMUNITY_ID] = df[COMMUNITY_ID].astype(int)
    df[COMMUNITY_LEVEL] = df[COMMUNITY_LEVEL].astype(int)
    df[COMMUNITY_CHILDREN] = df[COMMUNITY_CHILDREN].apply(_split_list_column)
    if ENTITY_IDS in df.columns:
        df[ENTITY_IDS] = df[ENTITY_IDS].apply(_split_list_column)
    if RELATIONSHIP_IDS in df.columns:
        df[RELATIONSHIP_IDS] = df[RELATIONSHIP_IDS].apply(_split_list_column)
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)
    df[PERIOD] = df[PERIOD].astype(str)
    df[SIZE] = df[SIZE].astype(int)

    return df


def community_reports_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the community reports dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    df[COMMUNITY_ID] = df[COMMUNITY_ID].astype(int)
    df[COMMUNITY_LEVEL] = df[COMMUNITY_LEVEL].astype(int)
    df[COMMUNITY_CHILDREN] = df[COMMUNITY_CHILDREN].apply(_split_list_column)
    df[RATING] = df[RATING].astype(float)
    df[FINDINGS] = df[FINDINGS].apply(_split_list_column)
    df[SIZE] = df[SIZE].astype(int)

    return df


def covariates_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the covariates dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)

    return df


def text_units_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the text units dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    df[N_TOKENS] = df[N_TOKENS].astype(int)
    if ENTITY_IDS in df.columns:
        df[ENTITY_IDS] = df[ENTITY_IDS].apply(_split_list_column)
    if RELATIONSHIP_IDS in df.columns:
        df[RELATIONSHIP_IDS] = df[RELATIONSHIP_IDS].apply(_split_list_column)
    if COVARIATE_IDS in df.columns:
        df[COVARIATE_IDS] = df[COVARIATE_IDS].apply(_split_list_column)

    return df


def documents_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the documents dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)

    return df
