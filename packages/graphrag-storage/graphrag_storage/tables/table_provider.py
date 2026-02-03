# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Abstract base class for table providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

    from .table import Table


class TableProvider(ABC):
    """Provide a table-based storage interface with support for DataFrames and row dictionaries."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Create a table provider instance.

        Args
        ----
            **kwargs: Any
                Keyword arguments for initialization, may include underlying Storage instance.
        """

    @abstractmethod
    async def read_dataframe(self, table_name: str) -> pd.DataFrame:
        """Read entire table as a pandas DataFrame.

        Args
        ----
            table_name: str
                The name of the table to read.

        Returns
        -------
            pd.DataFrame:
                The table data as a DataFrame.
        """

    @abstractmethod
    async def write_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Write entire table from a pandas DataFrame.

        Args
        ----
            table_name: str
                The name of the table to write.
            df: pd.DataFrame
                The DataFrame to write as a table.
        """

    @abstractmethod
    async def has_dataframe(self, table_name: str) -> bool:
        """Check if a table exists in the provider.

        Args
        ----
            table_name: str
                The name of the table to check.

        Returns
        -------
            bool:
                True if the table exists, False otherwise.
        """

    @abstractmethod
    def find_tables(self) -> list[str]:
        """Find all table names in the provider.

        Returns
        -------
            list[str]:
                List of table names (without file extensions).
        """

    @abstractmethod
    def open(
        self, table_name: str, context: dict[str, Any] | None = None
    ) -> Table:
        """Open a table for streaming row-by-row access.

        Args
        ----
            table_name: str
                The name of the table to open.
            context: dict[str, Any] | None
                Optional context for multi-dataset scenarios. Can include
                tenant_id, dataset_id, or other provider-specific metadata.

        Examples
        --------
                    {"dataset_id": "abc123", "tenant_id": "tenant_x"}
                    {"database": "production", "schema": "public"}

        Returns
        -------
            Table:
                Table instance supporting iteration and row writes.
                Should be used with async context manager for automatic cleanup.

        Examples
        --------
            >>> async with provider.open("documents") as table:
            ...     for row in table:
            ...         print(row["id"])
        """
