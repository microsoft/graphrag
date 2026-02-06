# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import unittest
from io import StringIO

import pandas as pd
import pytest
from graphrag_storage import (
    StorageConfig,
    StorageType,
    create_storage,
)
from graphrag_storage.tables.csv_table_provider import CSVTableProvider


class TestCSVTableProvider(unittest.IsolatedAsyncioTestCase):
    """Test suite for CSVTableProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = create_storage(
            StorageConfig(
                type=StorageType.Memory,
            )
        )
        self.table_provider = CSVTableProvider(storage=self.storage)

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.storage.clear()

    async def test_write_and_read(self):
        """Test writing and reading a DataFrame."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
        })

        await self.table_provider.write_dataframe("users", df)
        result = await self.table_provider.read_dataframe("users")

        pd.testing.assert_frame_equal(result, df)

    async def test_read_nonexistent_table_raises_error(self):
        """Test that reading a nonexistent table raises ValueError."""
        with pytest.raises(
            ValueError, match=r"Could not find nonexistent\.csv in storage!"
        ):
            await self.table_provider.read_dataframe("nonexistent")

    async def test_empty_dataframe(self):
        """Test writing and reading an empty DataFrame."""
        df = pd.DataFrame()

        await self.table_provider.write_dataframe("empty", df)
        result = await self.table_provider.read_dataframe("empty")

        pd.testing.assert_frame_equal(result, df)

    async def test_dataframe_with_multiple_types(self):
        """Test DataFrame with multiple column types."""
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
        })

        await self.table_provider.write_dataframe("mixed", df)
        result = await self.table_provider.read_dataframe("mixed")

        pd.testing.assert_frame_equal(result, df)

    async def test_storage_persistence(self):
        """Test that data is persisted in underlying storage."""
        df = pd.DataFrame({"x": [1, 2, 3]})

        await self.table_provider.write_dataframe("test", df)

        assert await self.storage.has("test.csv")

        csv_data = await self.storage.get("test.csv", as_bytes=False)
        loaded_df = pd.read_csv(StringIO(csv_data))

        pd.testing.assert_frame_equal(loaded_df, df)

    async def test_has(self):
        """Test has() method for checking table existence."""
        df = pd.DataFrame({"a": [1, 2, 3]})

        # Table doesn't exist yet
        assert not await self.table_provider.has("test_table")

        # Write the table
        await self.table_provider.write_dataframe("test_table", df)

        # Now it exists
        assert await self.table_provider.has("test_table")

    async def test_list(self):
        """Test listing all tables in storage."""
        # Initially empty
        assert self.table_provider.list() == []

        # Create some tables
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"b": [4, 5, 6]})
        df3 = pd.DataFrame({"c": [7, 8, 9]})

        await self.table_provider.write_dataframe("table1", df1)
        await self.table_provider.write_dataframe("table2", df2)
        await self.table_provider.write_dataframe("table3", df3)

        # List tables
        tables = self.table_provider.list()
        assert len(tables) == 3
        assert set(tables) == {"table1", "table2", "table3"}
