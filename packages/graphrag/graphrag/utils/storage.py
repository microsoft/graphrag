# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Storage functions for the GraphRAG run module."""

import logging

import pandas as pd
from graphrag_storage import ParquetTableProvider, Storage

logger = logging.getLogger(__name__)


async def load_table_from_storage(name: str, storage: Storage) -> pd.DataFrame:
    """Load a parquet from the storage instance."""
    table_provider = ParquetTableProvider(storage)
    return await table_provider.read_dataframe(name)


async def write_table_to_storage(
    table: pd.DataFrame, name: str, storage: Storage
) -> None:
    """Write a table to storage."""
    table_provider = ParquetTableProvider(storage)
    await table_provider.write_dataframe(name, table)


async def delete_table_from_storage(name: str, storage: Storage) -> None:
    """Delete a table to storage."""
    await storage.delete(f"{name}.parquet")


async def storage_has_table(name: str, storage: Storage) -> bool:
    """Check if a table exists in storage."""
    return await storage.has(f"{name}.parquet")
