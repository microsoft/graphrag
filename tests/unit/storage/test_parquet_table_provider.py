# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import unittest
from io import BytesIO

import pandas as pd
import pytest
from graphrag_storage import (
    StorageConfig,
    StorageType,
    create_storage,
)
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


class TestParquetTableProvider(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.storage = create_storage(
            StorageConfig(
                type=StorageType.Memory,
            )
        )
        self.table_provider = ParquetTableProvider(storage=self.storage)

    async def asyncTearDown(self):
        await self.storage.clear()

    async def test_write_and_read(self):
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
        })

        await self.table_provider.write_dataframe("users", df)
        result = await self.table_provider.read_dataframe("users")

        pd.testing.assert_frame_equal(result, df)

    async def test_read_nonexistent_table_raises_error(self):
        with pytest.raises(
            ValueError, match=r"Could not find nonexistent\.parquet in storage!"
        ):
            await self.table_provider.read_dataframe("nonexistent")

    async def test_empty_dataframe(self):
        df = pd.DataFrame()

        await self.table_provider.write_dataframe("empty", df)
        result = await self.table_provider.read_dataframe("empty")

        pd.testing.assert_frame_equal(result, df)

    async def test_dataframe_with_multiple_types(self):
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
        df = pd.DataFrame({"x": [1, 2, 3]})

        await self.table_provider.write_dataframe("test", df)

        assert await self.storage.has("test.parquet")

        parquet_bytes = await self.storage.get("test.parquet", as_bytes=True)
        loaded_df = pd.read_parquet(BytesIO(parquet_bytes))

        pd.testing.assert_frame_equal(loaded_df, df)

    async def test_has(self):
        df = pd.DataFrame({"a": [1, 2, 3]})

        # Table doesn't exist yet
        assert not await self.table_provider.has("test_table")

        # Write the table
        await self.table_provider.write_dataframe("test_table", df)

        # Now it exists
        assert await self.table_provider.has("test_table")
