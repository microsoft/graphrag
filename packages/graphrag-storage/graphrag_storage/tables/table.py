# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Table abstraction for streaming row-by-row access."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from types import TracebackType
from typing import Any

from typing_extensions import Self

RowTransformer = Callable[[dict[str, Any]], Any]


class Table(ABC):
    """Abstract base class for streaming table access.

    Provides row-by-row iteration and write capabilities for memory-efficient
    processing of large datasets. Supports async context manager protocol for
    automatic resource cleanup.

    Examples
    --------
        Reading rows as dicts:
        >>> async with (
        ...     provider.open(
        ...         "documents"
        ...     ) as table
        ... ):
        ...     async for (
        ...         row
        ...     ) in table:
        ...         process(row)

        With Pydantic model as transformer:
        >>> async with (
        ...     provider.open(
        ...         "entities",
        ...         Entity,
        ...     ) as table
        ... ):
        ...     async for entity in table:  # yields Entity instances
        ...         print(
        ...             entity.name
        ...         )
    """

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[Any]:
        """Yield rows asynchronously, transformed if transformer provided.

        Yields
        ------
            Any:
                Each row, either as dict or transformed type (e.g., Pydantic model).
        """
        ...

    @abstractmethod
    async def length(self) -> int:
        """Return number of rows asynchronously.

        Returns
        -------
            int:
                Number of rows in the table.
        """

    @abstractmethod
    async def has(self, row_id: str) -> bool:
        """Check if a row with the given ID exists.

        Args
        ----
            row_id: The ID value to search for.

        Returns
        -------
            bool:
                True if a row with matching ID exists.
        """

    @abstractmethod
    async def write(self, row: dict[str, Any]) -> None:
        """Write a single row to the table.

        Args
        ----
            row: Dictionary representing a single row to write.
        """

    @abstractmethod
    async def close(self) -> None:
        """Flush buffered writes and release resources.

        This method is called automatically when exiting the async context
        manager, but can also be called explicitly.
        """

    async def __aenter__(self) -> Self:
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
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager, ensuring close() is called.

        Args
        ----
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.close()
