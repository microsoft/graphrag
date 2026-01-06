# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Shared column processing for structured input files."""

import logging

import pandas as pd

from graphrag.index.utils.hashing import gen_sha512_hash

logger = logging.getLogger(__name__)


def process_data_columns(
    documents: pd.DataFrame,
    path: str,
    text_column: str | None,
    title_column: str | None,
) -> pd.DataFrame:
    """Process configured data columns of a DataFrame."""
    if "id" not in documents.columns:
        documents["id"] = documents.apply(
            lambda x: gen_sha512_hash(x, x.keys()), axis=1
        )
    if text_column is not None and "text" not in documents.columns:
        if text_column not in documents.columns:
            logger.warning(
                "text_column %s not found in csv file %s",
                text_column,
                path,
            )
        else:
            documents["text"] = documents.apply(lambda x: x[text_column], axis=1)
    if title_column is not None:
        if title_column not in documents.columns:
            logger.warning(
                "title_column %s not found in csv file %s",
                title_column,
                path,
            )
        else:
            documents["title"] = documents.apply(lambda x: x[title_column], axis=1)
    else:
        documents["title"] = documents.apply(lambda _: path, axis=1)
    return documents
