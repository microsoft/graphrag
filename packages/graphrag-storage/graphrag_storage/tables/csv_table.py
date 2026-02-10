# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT Licenses

"""A CSV-based implementation of the Table abstraction for streaming row access."""

import csv
import inspect
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import aiofiles

from graphrag_storage import Storage
from graphrag_storage.file_storage import FileStorage
from graphrag_storage.tables.table import RowTransformer, Table


def _identity(row: dict[str, Any]) -> Any:
    """Return row unchanged (default transformer)."""
    return row


def _apply_transformer(transformer: RowTransformer, row: dict[str, Any]) -> Any:
    """Apply transformer to row, handling both callables and classes.

    If transformer is a class (e.g., Pydantic model), calls it with **row.
    Otherwise calls it with row as positional argument.
    """
    if inspect.isclass(transformer):
        return transformer(**row)
    return transformer(row)


class CSVTable(Table):
    """Row-by-row streaming interface for CSV tables."""

    def __init__(
        self,
        storage: Storage,
        table_name: str,
        transformer: RowTransformer | None = None,
    ):
        """Initialize with storage backend and table name.

        Args:
            storage: Storage instance (File, Blob, or Cosmos)
            table_name: Name of the table (e.g., "documents")
            transformer: Optional callable to transform each row before
                yielding. Receives a dict, returns a transformed dict.
                Defaults to identity (no transformation).
        """
        self._storage = storage
        self._table_name = table_name
        self._file_key = f"{table_name}.csv"
        self._transformer = transformer or _identity

    def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate through rows one at a time.

        The transformer is applied to each row before yielding.
        If transformer is a Pydantic model, yields model instances.

        Yields
        ------
            Any:
                Each row as dict or transformed type (e.g., Pydantic model).
        """
        return self._aiter_impl()

    async def _aiter_impl(self) -> AsyncIterator[Any]:
        """Implement async iteration over rows."""
        if isinstance(self._storage, FileStorage):
            file_path = self._storage.get_path(self._file_key)
            with Path.open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield _apply_transformer(self._transformer, row)

    async def length(self) -> int:
        """Return the number of rows in the table."""
        if isinstance(self._storage, FileStorage):
            file_path = self._storage.get_path(self._file_key)
            count = 0
            async with aiofiles.open(file_path, "rb") as f:
                while True:
                    chunk = await f.read(65536)
                    if not chunk:
                        break
                    count += chunk.count(b"\n")
            return count - 1
        return 0

    async def has(self, row_id: str) -> bool:
        """Check if row with given ID exists."""
        async for row in self:
            # Handle both dict and object (e.g., Pydantic model)
            if isinstance(row, dict):
                if row.get("id") == row_id:
                    return True
            elif getattr(row, "id", None) == row_id:
                return True
        return False

    async def close(self) -> None:
        """Flush buffered writes and release resources.

        No-op for CSV tables since rows are read on demand
        and no persistent connections are held open.
        """
