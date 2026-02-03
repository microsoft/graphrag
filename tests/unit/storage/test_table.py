# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Unit tests for Table abstraction and ParquetTable implementation."""

import unittest

import pandas as pd
import pytest
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


class TestParquetTable(unittest.IsolatedAsyncioTestCase):
    """Test suite for ParquetTable streaming implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = create_storage(StorageConfig(type=StorageType.Memory))
        self.table_provider = ParquetTableProvider(storage=self.storage)

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.storage.clear()

    async def test_table_write_and_read_streaming(self):
        """Test writing rows incrementally and reading them back."""
        # Write rows one at a time
        async with self.table_provider.open("users") as table:
            await table.write({"id": 1, "name": "Alice", "age": 30})
            await table.write({"id": 2, "name": "Bob", "age": 25})
            await table.write({"id": 3, "name": "Charlie", "age": 35})

        # Read back and verify
        async with self.table_provider.open("users") as table:
            rows = list(table)
            assert len(rows) == 3
            assert rows[0]["name"] == "Alice"
            assert rows[1]["name"] == "Bob"
            assert rows[2]["name"] == "Charlie"

    async def test_table_iteration(self):
        """Test iterating over table rows."""
        # Create initial data using dataframe
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": ["a", "b", "c", "d", "e"],
        })
        await self.table_provider.write_dataframe("data", df)

        # Iterate and collect
        async with self.table_provider.open("data") as table:
            collected = []
            for row in table:
                collected.append(row["value"])

            assert collected == ["a", "b", "c", "d", "e"]

    async def test_table_length(self):
        """Test __len__ method."""
        # Write some data
        df = pd.DataFrame({"id": [1, 2, 3]})
        await self.table_provider.write_dataframe("test", df)

        async with self.table_provider.open("test") as table:
            assert len(table) == 3

    async def test_table_context_manager_closes(self):
        """Test that context manager calls close() automatically."""
        # Write data in context
        async with self.table_provider.open("auto_close") as table:
            await table.write({"id": 1, "data": "test"})
            # Don't call close() explicitly

        # Verify data was flushed
        result = await self.table_provider.read_dataframe("auto_close")
        assert len(result) == 1
        assert result.iloc[0]["data"] == "test"

    async def test_table_write_buffer_accumulation(self):
        """Test that writes accumulate in buffer before flush."""
        table = self.table_provider.open("buffered")

        # Write multiple rows
        await table.write({"id": 1})
        await table.write({"id": 2})
        await table.write({"id": 3})

        # Before close, data shouldn't exist in storage
        assert not await self.table_provider.has_dataframe("buffered")

        # After close, data should be persisted
        await table.close()
        assert await self.table_provider.has_dataframe("buffered")

        result = await self.table_provider.read_dataframe("buffered")
        assert len(result) == 3

    async def test_table_read_nonexistent_initializes_empty(self):
        """Test opening nonexistent table for writing."""
        async with self.table_provider.open("new_table") as table:
            # Should not raise error
            assert len(table) == 0
            await table.write({"id": 1, "value": "first"})

        # Verify it was created
        result = await self.table_provider.read_dataframe("new_table")
        assert len(result) == 1

    async def test_table_context_parameter_logs_warning(self):
        """Test that context parameter logs warning for ParquetTableProvider."""
        # This should log a warning but not fail
        async with self.table_provider.open(
            "test", context={"tenant_id": "abc"}
        ) as table:
            await table.write({"id": 1})

        # Should work normally despite context being ignored
        result = await self.table_provider.read_dataframe("test")
        assert len(result) == 1

    async def test_table_mixed_types(self):
        """Test table with various data types."""
        async with self.table_provider.open("mixed") as table:
            await table.write({
                "int_col": 42,
                "float_col": 3.14,
                "str_col": "hello",
                "bool_col": True,
                "none_col": None,
            })

        async with self.table_provider.open("mixed") as table:
            row = next(iter(table))
            assert row["int_col"] == 42
            assert row["float_col"] == 3.14
            assert row["str_col"] == "hello"
            assert row["bool_col"] is True
            assert pd.isna(row["none_col"])

    async def test_table_iteration_without_context_raises(self):
        """Test that iteration without async context raises error."""
        df = pd.DataFrame({"id": [1, 2, 3]})
        await self.table_provider.write_dataframe("test", df)

        table = self.table_provider.open("test")

        # Should raise because not loaded
        with pytest.raises(RuntimeError, match="not loaded"):
            list(table)

    async def test_table_multiple_writes_same_session(self):
        """Test multiple write calls in same context."""
        async with self.table_provider.open("multi_write") as table:
            for i in range(100):
                await table.write({"id": i, "value": f"item_{i}"})

        result = await self.table_provider.read_dataframe("multi_write")
        assert len(result) == 100
        assert result.iloc[50]["value"] == "item_50"

    async def test_table_empty_write_no_error(self):
        """Test that opening and closing without writes doesn't error."""
        async with self.table_provider.open("empty") as table:
            pass  # No writes

        # Should not create empty table
        assert not await self.table_provider.has_dataframe("empty")

    async def test_backward_compatibility_with_dataframe_methods(self):
        """Ensure new streaming methods don't break existing DataFrame API."""
        # Old way still works
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        await self.table_provider.write_dataframe("legacy", df)

        result = await self.table_provider.read_dataframe("legacy")
        pd.testing.assert_frame_equal(result, df)

        # New way also works on same data
        async with self.table_provider.open("legacy") as table:
            rows = list(table)
            assert len(rows) == 3


if __name__ == "__main__":
    unittest.main()
