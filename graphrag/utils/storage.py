# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Storage functions for the GraphRAG run module."""

import logging
from io import BytesIO

import pandas as pd

from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


async def load_table_from_storage(name: str, storage: PipelineStorage) -> pd.DataFrame:
    """Load a parquet from the storage instance."""
    if not await storage.has(name):
        msg = f"Could not find {name} in storage!"
        raise ValueError(msg)
    try:
        log.info("reading table from storage: %s", name)
        return pd.read_parquet(BytesIO(await storage.get(name, as_bytes=True)))
    except Exception:
        log.exception("error loading table from storage: %s", name)
        raise


async def write_table_to_storage(
    table: pd.DataFrame, name: str, storage: PipelineStorage
) -> None:
    """Write a table to storage."""
    await storage.set(name, table.to_parquet())
