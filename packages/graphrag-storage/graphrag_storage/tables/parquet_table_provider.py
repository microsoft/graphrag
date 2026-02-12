# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parquet-based table provider implementation."""

import logging
import re
from io import BytesIO

import pandas as pd

from graphrag_storage.storage import Storage
from graphrag_storage.tables.parquet_table import ParquetTable
from graphrag_storage.tables.table import RowTransformer, Table
from graphrag_storage.tables.table_provider import TableProvider

logger = logging.getLogger(__name__)


class ParquetTableProvider(TableProvider):
    """Table provider that stores tables as Parquet files using an underlying Storage instance.

    This provider converts between pandas DataFrames and Parquet format,
    storing the data through a Storage backend (file, blob, cosmos, etc.).
    """

    def __init__(self, storage: Storage, **kwargs) -> None:
        """Initialize the Parquet table provider with an underlying storage instance.

        Args
        ----
            storage: Storage
                The storage instance to use for reading and writing Parquet files.
            **kwargs: Any
                Additional keyword arguments (currently unused).
        """
        self._storage = storage

    async def read_dataframe(self, table_name: str) -> pd.DataFrame:
        """Read a table from storage as a pandas DataFrame.

        Args
        ----
            table_name: str
                The name of the table to read. The file will be accessed as '{table_name}.parquet'.

        Returns
        -------
            pd.DataFrame:
                The table data loaded from the Parquet file.

        Raises
        ------
            ValueError:
                If the table file does not exist in storage.
            Exception:
                If there is an error reading or parsing the Parquet file.
        """
        filename = f"{table_name}.parquet"
        if not await self._storage.has(filename):
            msg = f"Could not find {filename} in storage!"
            raise ValueError(msg)
        try:
            logger.info("reading table from storage: %s", filename)
            return pd.read_parquet(
                BytesIO(await self._storage.get(filename, as_bytes=True))
            )
        except Exception:
            logger.exception("error loading table from storage: %s", filename)
            raise

    async def write_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Write a pandas DataFrame to storage as a Parquet file.

        Args
        ----
            table_name: str
                The name of the table to write. The file will be saved as '{table_name}.parquet'.
            df: pd.DataFrame
                The DataFrame to write to storage.
        """
        await self._storage.set(f"{table_name}.parquet", df.to_parquet())

    async def has(self, table_name: str) -> bool:
        """Check if a table exists in storage.

        Args
        ----
            table_name: str
                The name of the table to check.

        Returns
        -------
            bool:
                True if the table exists, False otherwise.
        """
        return await self._storage.has(f"{table_name}.parquet")

    def list(self) -> list[str]:
        """List all table names in storage.

        Returns
        -------
            list[str]:
                List of table names (without .parquet extension).
        """
        return [
            file.replace(".parquet", "")
            for file in self._storage.find(re.compile(r"\.parquet$"))
        ]

    def open(
        self,
        table_name: str,
        transformer: RowTransformer | None = None,
        truncate: bool = True,
    ) -> Table:
        """Open a table for streaming row operations.

        Returns a ParquetTable that simulates streaming by loading the
        DataFrame and iterating rows, or accumulating writes for batch output.

        Args
        ----
            table_name: str
                The name of the table to open.
            transformer: RowTransformer | None
                Optional callable to transform each row on read.
            truncate: bool
                If True (default), overwrite existing file on close.
                If False, append new rows to existing file.

        Returns
        -------
            Table:
                A ParquetTable instance for row-by-row access.
        """
        return ParquetTable(self._storage, table_name, transformer, truncate=truncate)
