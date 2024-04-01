#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing load_input method definition."""
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast

import pandas as pd

from graphrag.index.config import PipelineInputConfig, PipelineInputStorageType
from graphrag.index.progress import NullProgressReporter, ProgressReporter
from graphrag.index.storage import (
    BlobPipelineStorage,
    FilePipelineStorage,
)

from .csv import input_type as csv
from .csv import load as load_csv
from .text import input_type as text
from .text import load as load_text

log = logging.getLogger(__name__)
loaders: dict[str, Callable[..., Awaitable[pd.DataFrame]]] = {
    text: load_text,
    csv: load_csv,
}


async def load_input(
    config: PipelineInputConfig,
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

    match config.storage_type:
        case PipelineInputStorageType.blob:
            log.info("using blob storage input")
            if config.connection_string is None or config.container_name is None:
                msg = "Connection string and container name required for blob storage"
                raise ValueError(msg)
            storage = BlobPipelineStorage(
                connection_string=config.connection_string,
                container_name=config.container_name,
                path_prefix=config.base_dir,
            )
        case PipelineInputStorageType.file:
            log.info("using file storage for input")
            storage = FilePipelineStorage(
                root_dir=str(Path(root_dir) / (config.base_dir or ""))
            )
        case _:
            log.info("using file storage for input")
            storage = FilePipelineStorage(
                root_dir=str(Path(root_dir) / (config.base_dir or ""))
            )

    if config.type in loaders:
        progress = progress_reporter.child(
            f"Loading Input ({config.type})", transient=False
        )
        loader = loaders[config.type]
        results = await loader(config, progress, storage)
        return cast(pd.DataFrame, results)

    msg = f"Unknown input type {config.type}"
    raise ValueError(msg)
