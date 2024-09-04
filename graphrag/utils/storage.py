# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Storage functions for the GraphRAG run module."""

import logging
from io import BytesIO
from pathlib import Path

import pandas as pd

from graphrag.index.config.storage import (
    PipelineFileStorageConfig,
    PipelineStorageConfigTypes,
)
from graphrag.index.storage import load_storage
from graphrag.index.storage.typing import PipelineStorage

log = logging.getLogger(__name__)


def _create_storage(
    config: PipelineStorageConfigTypes | None, root_dir: str
) -> PipelineStorage:
    """Create the storage for the pipeline.

    Parameters
    ----------
    config : PipelineStorageConfigTypes
        The storage configuration.
    root_dir : str
        The root directory.

    Returns
    -------
    PipelineStorage
        The pipeline storage.
    """
    return load_storage(
        config or PipelineFileStorageConfig(base_dir=str(Path(root_dir) / "output"))
    )


async def _load_table_from_storage(name: str, storage: PipelineStorage) -> pd.DataFrame:
    if not await storage.has(name):
        msg = f"Could not find {name} in storage!"
        raise ValueError(msg)
    try:
        log.info("read table from storage: %s", name)
        return pd.read_parquet(BytesIO(await storage.get(name, as_bytes=True)))
    except Exception:
        log.exception("error loading table from storage: %s", name)
        raise
