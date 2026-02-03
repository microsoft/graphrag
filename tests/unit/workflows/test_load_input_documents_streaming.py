# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Tests for load_input_documents workflow with streaming support."""

import unittest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
from graphrag.index.workflows.load_input_documents import (
    load_input_documents_streaming,
)
from graphrag_input import TextDocument
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


class TestLoadInputDocumentsStreaming(unittest.IsolatedAsyncioTestCase):
    """Test suite for streaming load_input_documents workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = create_storage(StorageConfig(type=StorageType.Memory))
        self.table_provider = ParquetTableProvider(storage=self.storage)

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.storage.clear()

    async def test_load_input_documents_streaming_basic(self):
        """Test basic streaming document loading."""
        # Create mock input reader
        mock_reader = MagicMock()
        mock_documents = [
            TextDocument(
                id="doc1",
                text="This is document 1",
                title="Document 1",
                creation_date="2025-01-29",
                raw_data={"source": "test"},
            ),
            TextDocument(
                id="doc2",
                text="This is document 2",
                title="Document 2",
                creation_date="2025-01-29",
                raw_data={"source": "test"},
            ),
            TextDocument(
                id="doc3",
                text="This is document 3",
                title="Document 3",
                creation_date="2025-01-29",
                raw_data={"source": "test"},
            ),
        ]
        mock_reader.read_files = AsyncMock(return_value=mock_documents)

        # Execute streaming load
        count = await load_input_documents_streaming(mock_reader, self.table_provider)

        # Verify
        assert count == 3

        # Read back and verify data
        result = await self.table_provider.read_dataframe("documents")
        assert len(result) == 3
        assert result.iloc[0]["id"] == "doc1"
        assert result.iloc[1]["id"] == "doc2"
        assert result.iloc[2]["id"] == "doc3"
        assert result.iloc[0]["text"] == "This is document 1"

    async def test_load_input_documents_streaming_large_batch(self):
        """Test streaming with larger document set."""
        # Create 500 mock documents
        mock_reader = MagicMock()
        mock_documents = [
            TextDocument(
                id=f"doc{i}",
                text=f"Document text {i}",
                title=f"Title {i}",
                creation_date="2025-01-29",
                raw_data={"index": i},
            )
            for i in range(500)
        ]
        mock_reader.read_files = AsyncMock(return_value=mock_documents)

        # Execute
        count = await load_input_documents_streaming(mock_reader, self.table_provider)

        # Verify
        assert count == 500
        result = await self.table_provider.read_dataframe("documents")
        assert len(result) == 500
        assert result.iloc[0]["id"] == "doc0"
        assert result.iloc[499]["id"] == "doc499"

    async def test_load_input_documents_preserves_all_fields(self):
        """Test that all TextDocument fields are preserved."""
        mock_reader = MagicMock()
        mock_documents = [
            TextDocument(
                id="test_doc",
                text="Sample text content",
                title="Sample Title",
                creation_date="2025-01-29T12:00:00",
                raw_data={"custom_field": "custom_value", "nested": {"key": "value"}},
            )
        ]
        mock_reader.read_files = AsyncMock(return_value=mock_documents)

        # Execute
        await load_input_documents_streaming(mock_reader, self.table_provider)

        # Verify all fields preserved
        result = await self.table_provider.read_dataframe("documents")
        row = result.iloc[0]
        assert row["id"] == "test_doc"
        assert row["text"] == "Sample text content"
        assert row["title"] == "Sample Title"
        assert row["creation_date"] == "2025-01-29T12:00:00"
        assert row["raw_data"]["custom_field"] == "custom_value"
        assert row["raw_data"]["nested"]["key"] == "value"

    async def test_load_input_documents_streaming_empty(self):
        """Test streaming with no documents."""
        mock_reader = MagicMock()
        mock_reader.read_files = AsyncMock(return_value=[])

        # Execute
        count = await load_input_documents_streaming(mock_reader, self.table_provider)

        # Verify
        assert count == 0

        # Table should not be created
        assert not await self.table_provider.has_dataframe("documents")

    async def test_load_input_documents_output_format_matches_dataframe(self):
        """Ensure streaming output format matches DataFrame-based approach."""
        mock_reader = MagicMock()
        mock_documents = [
            TextDocument(
                id="doc1",
                text="Text 1",
                title="Title 1",
                creation_date="2025-01-29",
                raw_data=None,
            ),
            TextDocument(
                id="doc2",
                text="Text 2",
                title="Title 2",
                creation_date="2025-01-29",
                raw_data={"extra": "data"},
            ),
        ]
        mock_reader.read_files = AsyncMock(return_value=mock_documents)

        # Create expected output using DataFrame approach
        expected_df = pd.DataFrame([asdict(doc) for doc in mock_documents])

        # Execute streaming
        await load_input_documents_streaming(mock_reader, self.table_provider)

        # Compare
        result = await self.table_provider.read_dataframe("documents")

        # Normalize for comparison (column order may differ)
        pd.testing.assert_frame_equal(
            result.sort_index(axis=1), expected_df.sort_index(axis=1), check_dtype=False
        )

    async def test_load_input_documents_streaming_with_none_raw_data(self):
        """Test documents with None raw_data field."""
        mock_reader = MagicMock()
        mock_documents = [
            TextDocument(
                id="doc1",
                text="Text",
                title="Title",
                creation_date="2025-01-29",
                raw_data=None,
            )
        ]
        mock_reader.read_files = AsyncMock(return_value=mock_documents)

        # Execute - should not raise error
        count = await load_input_documents_streaming(mock_reader, self.table_provider)

        assert count == 1
        result = await self.table_provider.read_dataframe("documents")
        assert pd.isna(result.iloc[0]["raw_data"]) or result.iloc[0]["raw_data"] is None


if __name__ == "__main__":
    unittest.main()
