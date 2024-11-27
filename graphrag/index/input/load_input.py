# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load_input method definition."""

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast

import pandas as pd

from graphrag.config.enums import InputType
from graphrag.config.models.input_config import InputConfig
from graphrag.index.config.input import PipelineInputConfig
from graphrag.index.input.csv import input_type as csv
from graphrag.index.input.csv import load as load_csv
from graphrag.index.input.text import input_type as text
from graphrag.index.input.text import load as load_text
from graphrag.index.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.index.storage.file_pipeline_storage import FilePipelineStorage
from graphrag.logging.base import ProgressReporter
from graphrag.logging.null_progress import NullProgressReporter

log = logging.getLogger(__name__)
loaders: dict[str, Callable[..., Awaitable[pd.DataFrame]]] = {
    text: load_text,
    csv: load_csv,
}


async def load_input(
    config: PipelineInputConfig | InputConfig,
    progress_reporter: ProgressReporter | None = None,
    root_dir: str | None = None,
) -> pd.DataFrame:
    """Load the input data for a pipeline."""
    root_dir = root_dir or ""
    log.info("loading input from root_dir=%s", config.base_dir)
    progress_reporter = progress_reporter or NullProgressReporter()

    if config is None:
        msg = "No input specified!"
        raise ValueError(msg)

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
        results = await loader(config, progress, storage)
        return cast(pd.DataFrame, results)

    msg = f"Unknown input type {config.file_type}"
    raise ValueError(msg)
