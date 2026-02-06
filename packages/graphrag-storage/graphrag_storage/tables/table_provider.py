# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Abstract base class for table providers."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


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
    async def has(self, table_name: str) -> bool:
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
    def list(self) -> list[str]:
        """List all table names in the provider.

        Returns
        -------
            list[str]:
                List of table names (without file extensions).
        """
