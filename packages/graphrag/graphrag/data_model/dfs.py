# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing dataframe processing utilities."""

from typing import Any

import pandas as pd

from graphrag.data_model.schemas import (
    CONVERSATION_ID,
    COMMUNITY_CHILDREN,
    COMMUNITY_ID,
    COMMUNITY_LEVEL,
    COVARIATE_IDS,
    EVIDENCE_COUNT,
    EDGE_DEGREE,
    EDGE_WEIGHT,
    ENTITY_IDS,
    FIRST_SEEN_TEXT_UNIT_ID,
    FIRST_SEEN_TIMESTAMP,
    FIRST_SEEN_TURN_INDEX,
    FINDINGS,
    LAST_SEEN_TEXT_UNIT_ID,
    LAST_SEEN_TIMESTAMP,
    LAST_SEEN_TURN_INDEX,
    N_TOKENS,
    NODE_DEGREE,
    NODE_FREQUENCY,
    PERIOD,
    START_TURN_INDEX,
    RATING,
    RELATIONSHIP_IDS,
    SHORT_ID,
    SIZE,
    CHUNK_INDEX_IN_CONVERSATION,
    CHUNK_INDEX_IN_DOCUMENT,
    TEXT_UNIT_IDS,
    TURN_INDEX,
    TURN_ROLE,
    TURN_TIMESTAMP,
    TURN_TIMESTAMP_END,
    TURN_TIMESTAMP_START,
    END_TURN_INDEX,
    INCLUDED_ROLES,
)


def _safe_int(series: pd.Series, fill: int = -1) -> pd.Series:
    """Convert a series to int, filling NaN values first."""
    return series.fillna(fill).astype(int)


def split_list_column(value: Any) -> list[Any]:
    r"""Split a column containing a list string into an actual list.

    Handles two CSV serialization formats:
    - Comma-separated (standard ``str(list)``): ``"['a', 'b']"``
    - Newline-separated (pandas ``to_csv`` of numpy arrays):
      ``"['a'\\n 'b']"``

    Both formats are stripped of brackets, quotes, and whitespace so
    that existing indexes produced by the old pandas-based indexer
    remain readable.
    """
    if isinstance(value, str):
        if not value:
            return []
        normalized = value.replace("\n", ",")
        items = [item.strip("[] '\"") for item in normalized.split(",")]
        return [item for item in items if item]
    return value


# Backward-compatible alias so internal callers keep working.
_split_list_column = split_list_column


def _coerce_temporal_evidence_df(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce shared temporal evidence columns when present."""
    if FIRST_SEEN_TURN_INDEX in df.columns:
        df[FIRST_SEEN_TURN_INDEX] = _safe_int(df[FIRST_SEEN_TURN_INDEX], 0)
    if LAST_SEEN_TURN_INDEX in df.columns:
        df[LAST_SEEN_TURN_INDEX] = _safe_int(df[LAST_SEEN_TURN_INDEX], 0)
    if EVIDENCE_COUNT in df.columns:
        df[EVIDENCE_COUNT] = _safe_int(df[EVIDENCE_COUNT], 0)
    if FIRST_SEEN_TIMESTAMP in df.columns:
        df[FIRST_SEEN_TIMESTAMP] = df[FIRST_SEEN_TIMESTAMP].astype(str)
    if LAST_SEEN_TIMESTAMP in df.columns:
        df[LAST_SEEN_TIMESTAMP] = df[LAST_SEEN_TIMESTAMP].astype(str)
    if FIRST_SEEN_TEXT_UNIT_ID in df.columns:
        df[FIRST_SEEN_TEXT_UNIT_ID] = df[FIRST_SEEN_TEXT_UNIT_ID].astype(str)
    if LAST_SEEN_TEXT_UNIT_ID in df.columns:
        df[LAST_SEEN_TEXT_UNIT_ID] = df[LAST_SEEN_TEXT_UNIT_ID].astype(str)
    return df


def entities_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the entities dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = _safe_int(df[SHORT_ID])
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)
    if NODE_FREQUENCY in df.columns:
        df[NODE_FREQUENCY] = _safe_int(df[NODE_FREQUENCY], 0)
    if NODE_DEGREE in df.columns:
        df[NODE_DEGREE] = _safe_int(df[NODE_DEGREE], 0)
    _coerce_temporal_evidence_df(df)

    return df


def relationships_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the relationships dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = _safe_int(df[SHORT_ID])
    if EDGE_WEIGHT in df.columns:
        df[EDGE_WEIGHT] = df[EDGE_WEIGHT].astype(float)
    if EDGE_DEGREE in df.columns:
        df[EDGE_DEGREE] = _safe_int(df[EDGE_DEGREE], 0)
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)
    _coerce_temporal_evidence_df(df)

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
    if TURN_INDEX in df.columns:
        df[TURN_INDEX] = _safe_int(df[TURN_INDEX], 0)
    if START_TURN_INDEX in df.columns:
        df[START_TURN_INDEX] = _safe_int(df[START_TURN_INDEX], 0)
    if END_TURN_INDEX in df.columns:
        df[END_TURN_INDEX] = _safe_int(df[END_TURN_INDEX], 0)
    if TURN_TIMESTAMP in df.columns:
        df[TURN_TIMESTAMP] = df[TURN_TIMESTAMP].astype(str)
    if TURN_TIMESTAMP_START in df.columns:
        df[TURN_TIMESTAMP_START] = df[TURN_TIMESTAMP_START].astype(str)
    if TURN_TIMESTAMP_END in df.columns:
        df[TURN_TIMESTAMP_END] = df[TURN_TIMESTAMP_END].astype(str)
    if TURN_ROLE in df.columns:
        df[TURN_ROLE] = df[TURN_ROLE].astype(str)
    if INCLUDED_ROLES in df.columns:
        df[INCLUDED_ROLES] = df[INCLUDED_ROLES].apply(_split_list_column)
    if CHUNK_INDEX_IN_DOCUMENT in df.columns:
        df[CHUNK_INDEX_IN_DOCUMENT] = _safe_int(df[CHUNK_INDEX_IN_DOCUMENT], 0)
    if CHUNK_INDEX_IN_CONVERSATION in df.columns:
        df[CHUNK_INDEX_IN_CONVERSATION] = _safe_int(
            df[CHUNK_INDEX_IN_CONVERSATION],
            0,
        )
    if CONVERSATION_ID in df.columns:
        df[CONVERSATION_ID] = df[CONVERSATION_ID].astype(str)

    return df


def documents_typed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the documents dataframe with correct types, in case it was stored in a weakly-typed format."""
    if SHORT_ID in df.columns:
        df[SHORT_ID] = df[SHORT_ID].astype(int)
    if TEXT_UNIT_IDS in df.columns:
        df[TEXT_UNIT_IDS] = df[TEXT_UNIT_IDS].apply(_split_list_column)
    if TURN_INDEX in df.columns:
        df[TURN_INDEX] = _safe_int(df[TURN_INDEX], 0)
    if TURN_TIMESTAMP in df.columns:
        df[TURN_TIMESTAMP] = df[TURN_TIMESTAMP].astype(str)
    if TURN_ROLE in df.columns:
        df[TURN_ROLE] = df[TURN_ROLE].astype(str)
    if CONVERSATION_ID in df.columns:
        df[CONVERSATION_ID] = df[CONVERSATION_ID].astype(str)

    return df
