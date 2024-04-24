# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing community report generation utilities."""

import pandas as pd

import graphrag.index.graph.extractors.community_reports.schemas as schemas
from graphrag.query.llm.text_utils import num_tokens


def set_context_size(df: pd.DataFrame) -> None:
    """Measure the number of tokens in the context."""
    df[schemas.CONTEXT_SIZE] = df[schemas.CONTEXT_STRING].apply(lambda x: num_tokens(x))


def set_context_exceeds_flag(df: pd.DataFrame, max_tokens: int) -> None:
    """Set a flag to indicate if the context exceeds the limit."""
    df[schemas.CONTEXT_EXCEED_FLAG] = df[schemas.CONTEXT_SIZE].apply(
        lambda x: x > max_tokens
    )


def get_levels(df: pd.DataFrame, level_column: str = schemas.NODE_LEVEL) -> list[int]:
    """Get the levels of the communities."""
    return sorted(df[level_column].notna().astype(int).unique().tolist(), reverse=True)
