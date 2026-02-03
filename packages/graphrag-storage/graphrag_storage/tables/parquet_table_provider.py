# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parquet-based table provider implementation."""

from __future__ import annotations

import logging
import re
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Iterator

    from graphrag_storage.storage import Storage

from .table import Table
from .table_provider import TableProvider

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

    async def has_dataframe(self, table_name: str) -> bool:
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

    def find_tables(self) -> list[str]:
        """Find all table names in storage.

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
        self, table_name: str, context: dict[str, Any] | None = None
    ) -> Table:
        """Open a table for streaming row-by-row access.

        Args
        ----
            table_name: str
                The name of the table to open.
            context: dict[str, Any] | None
                Optional context (ignored by ParquetTableProvider).
                File-based storage is single-tenant and does not use context.

        Returns
        -------
            Table:
                ParquetTable instance for streaming access.
        """
        if context:
            logger.warning(
                "Context provided to ParquetTableProvider.open() but will be ignored. "
                "File-based storage does not support multi-dataset context. "
                "Context: %s",
                context,
            )
        return ParquetTable(storage=self._storage, table_name=table_name)


class ParquetTable(Table):
    """Table implementation that reads/writes Parquet files with streaming support.

    Supports both read and write modes:
    - Read mode: Loads parquet into memory, yields rows via iteration
    - Write mode: Buffers rows in memory, writes parquet on close()

    The mode is determined automatically based on table existence when opened.
    """

    def __init__(self, storage: Storage, table_name: str) -> None:
        """Initialize ParquetTable.

        Args
        ----
            storage: Storage
                The underlying storage instance for reading/writing parquet files.
            table_name: str
                Name of the table (without .parquet extension).
        """
        self._storage = storage
        self._table_name = table_name
        self._filename = f"{table_name}.parquet"
        self._dataframe: pd.DataFrame | None = None
        self._write_buffer: list[dict[str, Any]] = []
        self._is_loaded = False

    async def _ensure_loaded(self) -> None:
        """Load the parquet file into memory if not already loaded."""
        if self._is_loaded:
            return

        if await self._storage.has(self._filename):
            try:
                logger.debug("Loading table for streaming: %s", self._filename)
                parquet_bytes = await self._storage.get(self._filename, as_bytes=True)
                self._dataframe = pd.read_parquet(BytesIO(parquet_bytes))
                self._is_loaded = True
                logger.info(
                    "Loaded table %s: %d rows", self._filename, len(self._dataframe)
                )
            except Exception:
                logger.exception("Error loading table for streaming: %s", self._filename)
                raise
        else:
            # Table doesn't exist yet - initialize empty for write mode
            self._dataframe = pd.DataFrame()
            self._is_loaded = True
            logger.debug(
                "Table %s does not exist, initialized for write mode", self._filename
            )

    def __len__(self) -> int:
        """Return number of rows in table.

        Returns
        -------
            int:
                Number of rows in loaded dataframe plus buffered writes.
        """
        df_len = len(self._dataframe) if self._dataframe is not None else 0
        return df_len + len(self._write_buffer)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield rows as dictionaries.

        Note: This is a synchronous method that requires the table to be
        loaded first. Call _ensure_loaded() before iteration or use async context.

        Yields
        ------
            dict[str, Any]:
                Each row as a dictionary.
        """
        if not self._is_loaded or self._dataframe is None:
            msg = f"Table {self._table_name} not loaded. Use async context manager."
            raise RuntimeError(msg)

        for _, row in self._dataframe.iterrows():
            yield row.to_dict()

    async def write(self, row: dict[str, Any]) -> None:
        """Write a single row to the table buffer.

        Args
        ----
            row: dict[str, Any]
                Row data as a dictionary.
        """
        self._write_buffer.append(row)
        logger.debug(
            "Buffered row for %s (buffer size: %d)",
            self._filename,
            len(self._write_buffer),
        )

    async def close(self) -> None:
        """Flush buffered writes to storage and release resources."""
        if self._write_buffer:
            try:
                logger.info(
                    "Flushing %d buffered rows to %s",
                    len(self._write_buffer),
                    self._filename,
                )
                df = pd.DataFrame(self._write_buffer)
                parquet_bytes = df.to_parquet()
                await self._storage.set(self._filename, parquet_bytes)
                logger.info("Successfully wrote %s", self._filename)
                self._write_buffer.clear()
            except Exception:
                logger.exception(
                    "Error flushing %d rows to %s",
                    len(self._write_buffer),
                    self._filename,
                )
                raise
        else:
            logger.debug("No buffered writes to flush for %s", self._filename)

    async def __aenter__(self) -> ParquetTable:
        """Enter async context manager, loading the table if needed.

        Returns
        -------
            ParquetTable:
                Self with table loaded.
        """
        await self._ensure_loaded()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager, flushing any buffered writes.

        Args
        ----
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.close()
