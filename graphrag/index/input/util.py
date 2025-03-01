# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Shared column processing for structured input files."""

import logging
import re
from typing import Any

import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.base import ProgressLogger
from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


async def load_files(
    loader: Any,
    config: InputConfig,
    storage: PipelineStorage,
    progress: ProgressLogger | None,
) -> pd.DataFrame:
    """Load files from storage and apply a loader function."""
    files = list(
        storage.find(
            re.compile(config.file_pattern),
            progress=progress,
            file_filter=config.file_filter,
        )
    )

    if len(files) == 0:
        msg = f"No {config.file_type} files found in {config.base_dir}"
        raise ValueError(msg)

    files_loaded = []

    for file, group in files:
        try:
            files_loaded.append(await loader(file, group))
        except Exception as e:  # noqa: BLE001 (catching Exception is fine here)
            log.warning("Warning! Error loading file %s. Skipping...", file)
            log.warning("Error: %s", e)

    log.info(
        "Found %d %s files, loading %d", len(files), config.file_type, len(files_loaded)
    )
    result = pd.concat(files_loaded)
    total_files_log = (
        f"Total number of unfiltered {config.file_type} rows: {len(result)}"
    )
    log.info(total_files_log)
    return result


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
            log.warning(
                "text_column %s not found in csv file %s",
                config.text_column,
                path,
            )
        else:
            documents["text"] = documents.apply(lambda x: x[config.text_column], axis=1)
    if config.title_column is not None:
        if config.title_column not in documents.columns:
            log.warning(
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
