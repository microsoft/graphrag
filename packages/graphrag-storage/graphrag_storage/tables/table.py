# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Table abstraction for streaming row-by-row access."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


class Table(ABC):
    """Abstract base class for streaming table access.
    
    Provides row-by-row iteration and write capabilities for memory-efficient
    processing of large datasets. Supports async context manager protocol for
    automatic resource cleanup.
    
    Examples
    --------
        Reading rows:
        >>> async with table_provider.open("documents") as table:
        ...     for row in table:
        ...         process(row)
        
        Writing rows:
        >>> async with table_provider.open("output") as table:
        ...     for item in items:
        ...         await table.write({"id": item.id, "value": item.value})
    """

    @abstractmethod
    def __len__(self) -> int:
        """Return number of rows in table.
        
        Returns
        -------
            int:
                Number of rows currently in the table.
        """

    @abstractmethod
    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield rows as dictionaries.
        
        Yields
        ------
            dict[str, Any]:
                Each row as a dictionary mapping column names to values.
        """

    @abstractmethod
    async def write(self, row: dict[str, Any]) -> None:
        """Write a single row to table buffer.
        
        Rows are buffered in memory until close() is called, at which point
        they are flushed to the underlying storage.
        
        Args
        ----
            row: dict[str, Any]
                Row data as a dictionary mapping column names to values.
        """

    @abstractmethod
    async def close(self) -> None:
        """Flush buffered writes and release resources.
        
        This method is called automatically when exiting the async context
        manager, but can also be called explicitly.
        """

    async def __aenter__(self) -> "Table":
        """Enter async context manager.
        
        Returns
        -------
            Table:
                Self for context manager usage.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager, ensuring close() is called.
        
        Args
        ----
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.close()
