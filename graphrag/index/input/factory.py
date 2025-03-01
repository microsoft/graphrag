# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_input method definition."""

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast

import pandas as pd

from graphrag.config.enums import InputFileType, InputType
from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.csv import load_csv
from graphrag.index.input.json import load_json
from graphrag.index.input.text import load_text
from graphrag.logger.base import ProgressLogger
from graphrag.logger.null_progress import NullProgressLogger
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage

log = logging.getLogger(__name__)
loaders: dict[str, Callable[..., Awaitable[pd.DataFrame]]] = {
    InputFileType.text: load_text,
    InputFileType.csv: load_csv,
    InputFileType.json: load_json,
}


async def create_input(
    config: InputConfig,
    progress_reporter: ProgressLogger | None = None,
    root_dir: str | None = None,
) -> pd.DataFrame:
    """Instantiate input data for a pipeline."""
    root_dir = root_dir or ""
    log.info("loading input from root_dir=%s", config.base_dir)
    progress_reporter = progress_reporter or NullProgressLogger()

    match config.type:
        case InputType.blob:
            log.info("using blob storage input")
            if config.container_name is None:
                msg = "Container name required for blob storage"
                raise ValueError(msg)
            if (
                config.connection_string is None
                and config.storage_account_blob_url is None
            ):
                msg = "Connection string or storage account blob url required for blob storage"
                raise ValueError(msg)
            storage = BlobPipelineStorage(
                connection_string=config.connection_string,
                storage_account_blob_url=config.storage_account_blob_url,
                container_name=config.container_name,
                path_prefix=config.base_dir,
            )
        case InputType.file:
            log.info("using file storage for input")
            storage = FilePipelineStorage(
                root_dir=str(Path(root_dir) / (config.base_dir or ""))
            )
        case _:
            log.info("using file storage for input")
            storage = FilePipelineStorage(
                root_dir=str(Path(root_dir) / (config.base_dir or ""))
            )

    if config.file_type in loaders:
        progress = progress_reporter.child(
            f"Loading Input ({config.file_type})", transient=False
        )
        loader = loaders[config.file_type]
        result = await loader(config, progress, storage)
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
