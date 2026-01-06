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
    id_column: str | None = None,
    title_column: str | None = None,
    text_column: str = "text",
) -> pd.DataFrame:
    """Process configured data columns of a DataFrame."""
    # id is optional - generate from harvest from df or hash from text
    if id_column is not None:
        documents["id"] = documents.apply(lambda x: x[id_column], axis=1)
    else:
        documents["id"] = documents.apply(
            lambda x: gen_sha512_hash(x, x.keys()), axis=1
        )

    # title is optional - harvest from df or use filename
    if title_column is not None:
        documents["title"] = documents.apply(lambda x: x[title_column], axis=1)
    else:
        documents["title"] = documents.apply(lambda _: path, axis=1)

    # text column is required - harvest from df
    documents["text"] = documents.apply(lambda x: x[text_column], axis=1)

    return documents
