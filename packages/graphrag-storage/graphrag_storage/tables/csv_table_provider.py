# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""CSV-based table provider implementation."""

import logging
import re
from io import StringIO

import pandas as pd

from graphrag_storage.file_storage import FileStorage
from graphrag_storage.storage import Storage
from graphrag_storage.tables.csv_table import CSVTable
from graphrag_storage.tables.table import RowTransformer
from graphrag_storage.tables.table_provider import TableProvider

logger = logging.getLogger(__name__)


class CSVTableProvider(TableProvider):
    """Table provider that stores tables as CSV files using an underlying Storage instance.

    This provider converts between pandas DataFrames and csv format,
    storing the data through a Storage backend (file, blob, cosmos, etc.).
    """

    def __init__(self, storage: Storage, **kwargs) -> None:
        """Initialize the CSV table provider with an underlying storage instance.

        Args
        ----
            storage: Storage
                The storage instance to use for reading and writing csv files.
            **kwargs: Any
                Additional keyword arguments (currently unused).
        """
        if not isinstance(storage, FileStorage):
            msg = "CSVTableProvider only works with FileStorage backends for now. "
            raise TypeError(msg)
        self._storage = storage

    async def read_dataframe(self, table_name: str) -> pd.DataFrame:
        """Read a table from storage as a pandas DataFrame.

        Args
        ----
            table_name: str
                The name of the table to read. The file will be accessed as '{table_name}.csv'.

        Returns
        -------
            pd.DataFrame:
                The table data loaded from the csv file.

        Raises
        ------
            ValueError:
                If the table file does not exist in storage.
            Exception:
                If there is an error reading or parsing the csv file.
        """
        filename = f"{table_name}.csv"
        if not await self._storage.has(filename):
            msg = f"Could not find {filename} in storage!"
            raise ValueError(msg)
        try:
            logger.info("reading table from storage: %s", filename)
            csv_data = await self._storage.get(filename, as_bytes=False)
            # Handle empty CSV (pandas can't parse files with no columns)
            if not csv_data or csv_data.strip() == "":
                return pd.DataFrame()
            return pd.read_csv(StringIO(csv_data), keep_default_na=False)
        except Exception:
            logger.exception("error loading table from storage: %s", filename)
            raise

    async def write_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Write a pandas DataFrame to storage as a CSV file.

        Args
        ----
            table_name: str
                The name of the table to write. The file will be saved as '{table_name}.csv'.
            df: pd.DataFrame
                The DataFrame to write to storage.
        """
        await self._storage.set(f"{table_name}.csv", df.to_csv(index=False))

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
        return await self._storage.has(f"{table_name}.csv")

    def list(self) -> list[str]:
        """List all table names in storage.

        Returns
        -------
            list[str]:
                List of table names (without .csv extension).
        """
        return [
            file.replace(".csv", "")
            for file in self._storage.find(re.compile(r"\.csv$"))
        ]

    def open(
        self,
        table_name: str,
        transformer: RowTransformer | None = None,
        truncate: bool = True,
        encoding: str = "utf-8",
    ) -> CSVTable:
        """Open table for streaming.

        Args:
            table_name: Name of the table to open
            transformer: Optional callable to transform each row
            truncate: If True, truncate file on first write
            encoding: Character encoding for reading/writing CSV files.
                Defaults to "utf-8".
        """
        return CSVTable(
            self._storage,
            table_name,
            transformer=transformer,
            truncate=truncate,
            encoding=encoding,
        )
