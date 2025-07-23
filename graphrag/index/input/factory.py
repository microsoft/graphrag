# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_input method definition."""

import logging
from collections.abc import Awaitable, Callable
from typing import cast

import pandas as pd

from graphrag.config.enums import InputFileType
from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.csv import load_csv
from graphrag.index.input.json import load_json
from graphrag.index.input.text import load_text
from graphrag.index.input.memory_csv import load_memory_csv
from graphrag.storage.pipeline_storage import PipelineStorage

logger = logging.getLogger(__name__)
loaders: dict[str, Callable[..., Awaitable[pd.DataFrame]]] = {
    InputFileType.text: load_text,
    InputFileType.csv: load_csv,
    InputFileType.json: load_json
}

in_memory_loaders: dict[str, Callable[..., Awaitable[pd.DataFrame]]] = {
    InputFileType.memory_csv: load_memory_csv
}


async def create_input(
    config: InputConfig,
    storage: PipelineStorage,
    input_files: list[pd.DataFrame] = list(),
) -> pd.DataFrame:
    """Instantiate input data for a pipeline."""
    logger.info("loading input from root_dir=%s", config.storage.base_dir)

    if config.file_type in loaders:
        logger.info("Loading Input %s from loaders", config.file_type)
        loader = loaders[config.file_type]
    elif config.file_type in in_memory_loaders:
        logger.info("Loading Input %s from in_memory_loaders", config.file_type)
        loader = in_memory_loaders[config.file_type]
    else:
        loader = None

    if loader is not None:
        if loader == load_memory_csv:            
            result = await loader(config, storage, input_files=input_files)
        else:
            result = await loader(config, storage)

        # Convert metadata columns to strings and collapse them into a JSON object
        if config.metadata:
            if all(col in result.columns for col in config.metadata):
                # Collapse the metadata columns into a single JSON object column
                result["metadata"] = result[config.metadata].apply(
                    lambda row: row.to_dict(), axis=1
                )
            else:
                value_error_msg = (
                    "One or more metadata columns not found in the DataFrame."
                )
                raise ValueError(value_error_msg)

            result[config.metadata] = result[config.metadata].astype(str)

        return cast("pd.DataFrame", result)

    msg = f"Unknown input type {config.file_type}"
    raise ValueError(msg)
