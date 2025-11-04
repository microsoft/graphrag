# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Shared column processing for structured input files."""

import logging

import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.utils.hashing import gen_sha512_hash

logger = logging.getLogger(__name__)


def process_data_columns(
    documents: pd.DataFrame, config: InputConfig, path: str
) -> pd.DataFrame:
    """Process configured data columns of a DataFrame."""
    if "id" not in documents.columns:
        documents["id"] = documents.apply(
            lambda x: gen_sha512_hash(x, x.keys()), axis=1
        )
    if config.text_column is not None and "text" not in documents.columns:
        if config.text_column not in documents.columns:
            logger.warning(
                "text_column %s not found in csv file %s",
                config.text_column,
                path,
            )
        else:
            documents["text"] = documents.apply(lambda x: x[config.text_column], axis=1)
    if config.title_column is not None:
        if config.title_column not in documents.columns:
            logger.warning(
                "title_column %s not found in csv file %s",
                config.title_column,
                path,
            )
        else:
            documents["title"] = documents.apply(
                lambda x: x[config.title_column], axis=1
            )
    else:
        documents["title"] = documents.apply(lambda _: path, axis=1)
    return documents
