# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Tests for create_final_documents workflow with streaming support."""

import unittest

import pandas as pd
from graphrag.index.workflows.create_final_documents import (
    create_final_documents_streaming,
)
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


class TestCreateFinalDocumentsStreaming(unittest.IsolatedAsyncioTestCase):
    """Test suite for streaming create_final_documents workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = create_storage(StorageConfig(type=StorageType.Memory))
        self.table_provider = ParquetTableProvider(storage=self.storage)

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.storage.clear()

    async def test_create_final_documents_streaming_basic(self):
        """Test basic streaming document finalization."""
        # Create test data
        documents_df = pd.DataFrame({
            "id": ["doc1", "doc2", "doc3"],
            "title": ["Title 1", "Title 2", "Title 3"],
            "text": ["Text 1", "Text 2", "Text 3"],
            "creation_date": ["2025-01-29", "2025-01-29", "2025-01-29"],
            "raw_data": [{"source": "test"}, None, {"source": "other"}],
        })
        
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2", "tu3", "tu4", "tu5"],
            "document_id": ["doc1", "doc1", "doc2", "doc2", "doc3"],
            "text": ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4", "Chunk 5"],
            "n_tokens": [10, 12, 11, 13, 9],
        })
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute streaming
        await create_final_documents_streaming(self.table_provider)
        
        # Verify
        result = await self.table_provider.read_dataframe("documents")
        assert len(result) == 3
        
        # Check doc1 has 2 text units
        doc1 = result[result["id"] == "doc1"].iloc[0]
        assert set(doc1["text_unit_ids"]) == {"tu1", "tu2"}
        assert doc1["title"] == "Title 1"
        
        # Check doc2 has 2 text units
        doc2 = result[result["id"] == "doc2"].iloc[0]
        assert set(doc2["text_unit_ids"]) == {"tu3", "tu4"}
        
        # Check doc3 has 1 text unit
        doc3 = result[result["id"] == "doc3"].iloc[0]
        assert set(doc3["text_unit_ids"]) == {"tu5"}

    async def test_create_final_documents_streaming_no_text_units(self):
        """Test documents with no associated text units."""
        documents_df = pd.DataFrame({
            "id": ["doc1", "doc2"],
            "title": ["Title 1", "Title 2"],
            "text": ["Text 1", "Text 2"],
            "creation_date": ["2025-01-29", "2025-01-29"],
            "raw_data": [None, None],
        })
        
        # Empty text_units
        text_units_df = pd.DataFrame({
            "id": [],
            "document_id": [],
            "text": [],
            "n_tokens": [],
        })
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute
        await create_final_documents_streaming(self.table_provider)
        
        # Verify - documents should have empty text_unit_ids
        result = await self.table_provider.read_dataframe("documents")
        assert len(result) == 2
        assert len(result.iloc[0]["text_unit_ids"]) == 0
        assert len(result.iloc[1]["text_unit_ids"]) == 0

    async def test_create_final_documents_streaming_preserves_fields(self):
        """Test that all required fields are preserved."""
        documents_df = pd.DataFrame({
            "id": ["doc1"],
            "title": ["Test Title"],
            "text": ["Test Text"],
            "creation_date": ["2025-01-29T12:00:00"],
            "raw_data": [{"custom": "data", "nested": {"key": "value"}}],
        })
        
        text_units_df = pd.DataFrame({
            "id": ["tu1"],
            "document_id": ["doc1"],
            "text": ["Chunk"],
            "n_tokens": [10],
        })
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute
        await create_final_documents_streaming(self.table_provider)
        
        # Verify all fields preserved
        result = await self.table_provider.read_dataframe("documents")
        row = result.iloc[0]
        
        assert row["id"] == "doc1"
        assert row["title"] == "Test Title"
        assert row["text"] == "Test Text"
        assert row["creation_date"] == "2025-01-29T12:00:00"
        assert row["raw_data"]["custom"] == "data"
        assert row["raw_data"]["nested"]["key"] == "value"
        assert "human_readable_id" in row
        assert "text_unit_ids" in row

    async def test_create_final_documents_streaming_human_readable_id(self):
        """Test that human_readable_id is assigned correctly."""
        documents_df = pd.DataFrame({
            "id": ["doc_c", "doc_a", "doc_b"],  # Non-sequential IDs
            "title": ["Title C", "Title A", "Title B"],
            "text": ["Text C", "Text A", "Text B"],
            "creation_date": ["2025-01-29"] * 3,
            "raw_data": [None, None, None],
        })
        
        text_units_df = pd.DataFrame({
            "id": [],
            "document_id": [],
            "text": [],
            "n_tokens": [],
        })
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute
        await create_final_documents_streaming(self.table_provider)
        
        # Verify human_readable_id is sequential
        result = await self.table_provider.read_dataframe("documents")
        assert set(result["human_readable_id"].tolist()) == {0, 1, 2}

    async def test_create_final_documents_streaming_large_dataset(self):
        """Test with larger dataset to verify streaming benefits."""
        # Create 500 documents
        documents_df = pd.DataFrame({
            "id": [f"doc{i}" for i in range(500)],
            "title": [f"Title {i}" for i in range(500)],
            "text": [f"Text {i}" for i in range(500)],
            "creation_date": ["2025-01-29"] * 500,
            "raw_data": [None] * 500,
        })
        
        # Create text units (2-5 per document)
        text_units = []
        tu_id = 0
        for doc_id in range(500):
            num_chunks = 2 + (doc_id % 4)  # 2-5 chunks
            for _ in range(num_chunks):
                text_units.append({
                    "id": f"tu{tu_id}",
                    "document_id": f"doc{doc_id}",
                    "text": f"Chunk {tu_id}",
                    "n_tokens": 10,
                })
                tu_id += 1
        
        text_units_df = pd.DataFrame(text_units)
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute
        await create_final_documents_streaming(self.table_provider)
        
        # Verify
        result = await self.table_provider.read_dataframe("documents")
        assert len(result) == 500
        
        # Spot check
        doc0 = result[result["id"] == "doc0"].iloc[0]
        assert len(doc0["text_unit_ids"]) == 2
        
        doc1 = result[result["id"] == "doc1"].iloc[0]
        assert len(doc1["text_unit_ids"]) == 3

    async def test_create_final_documents_streaming_id_type_conversion(self):
        """Test that document IDs are converted to strings."""
        # Start with numeric IDs
        documents_df = pd.DataFrame({
            "id": [1, 2, 3],
            "title": ["Title 1", "Title 2", "Title 3"],
            "text": ["Text 1", "Text 2", "Text 3"],
            "creation_date": ["2025-01-29"] * 3,
            "raw_data": [None, None, None],
        })
        
        text_units_df = pd.DataFrame({
            "id": ["tu1"],
            "document_id": [1],
            "text": ["Chunk"],
            "n_tokens": [10],
        })
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute
        await create_final_documents_streaming(self.table_provider)
        
        # Verify IDs are strings
        result = await self.table_provider.read_dataframe("documents")
        assert result.iloc[0]["id"] == "1"
        assert isinstance(result.iloc[0]["id"], str)

    async def test_create_final_documents_streaming_missing_raw_data(self):
        """Test documents without raw_data field."""
        documents_df = pd.DataFrame({
            "id": ["doc1"],
            "title": ["Title"],
            "text": ["Text"],
            "creation_date": ["2025-01-29"],
            # No raw_data field
        })
        
        text_units_df = pd.DataFrame({
            "id": [],
            "document_id": [],
            "text": [],
            "n_tokens": [],
        })
        
        await self.table_provider.write_dataframe("documents", documents_df)
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Execute - should handle missing raw_data gracefully
        await create_final_documents_streaming(self.table_provider)
        
        # Verify
        result = await self.table_provider.read_dataframe("documents")
        assert len(result) == 1
        # raw_data should be None or NaN
        assert pd.isna(result.iloc[0]["raw_data"]) or result.iloc[0]["raw_data"] is None


if __name__ == "__main__":
    unittest.main()
