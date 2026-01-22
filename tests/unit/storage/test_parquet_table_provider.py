# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import unittest
from io import BytesIO

import pandas as pd
import pytest
from graphrag_storage import ParquetTableProvider, StorageConfig, StorageType, create_storage


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
            "age": [30, 25, 35]
        })

        await self.table_provider.write("users", df)
        result = await self.table_provider.read("users")

        pd.testing.assert_frame_equal(result, df)

    async def test_read_nonexistent_table_raises_error(self):
        with pytest.raises(ValueError, match="Could not find nonexistent.parquet in storage!"):
            await self.table_provider.read("nonexistent")

    async def test_empty_dataframe(self):
        df = pd.DataFrame()

        await self.table_provider.write("empty", df)
        result = await self.table_provider.read("empty")

        pd.testing.assert_frame_equal(result, df)

    async def test_dataframe_with_multiple_types(self):
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True]
        })

        await self.table_provider.write("mixed", df)
        result = await self.table_provider.read("mixed")

        pd.testing.assert_frame_equal(result, df)

    async def test_storage_persistence(self):
        df = pd.DataFrame({"x": [1, 2, 3]})

        await self.table_provider.write("test", df)
        
        assert await self.storage.has("test.parquet")
        
        parquet_bytes = await self.storage.get("test.parquet", as_bytes=True)
        loaded_df = pd.read_parquet(BytesIO(parquet_bytes))
        
        pd.testing.assert_frame_equal(loaded_df, df)
