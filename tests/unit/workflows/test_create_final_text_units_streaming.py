# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Tests for create_final_text_units workflow with streaming support."""

import unittest

import pandas as pd
from graphrag.index.workflows.create_final_text_units import (
    create_final_text_units_streaming,
)
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


class TestCreateFinalTextUnitsStreaming(unittest.IsolatedAsyncioTestCase):
    """Test suite for streaming create_final_text_units workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = create_storage(StorageConfig(type=StorageType.Memory))
        self.table_provider = ParquetTableProvider(storage=self.storage)

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.storage.clear()

    async def test_create_final_text_units_streaming_basic(self):
        """Test basic streaming text unit finalization."""
        # Create test data
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2", "tu3"],
            "text": ["Text 1", "Text 2", "Text 3"],
            "document_id": ["doc1", "doc1", "doc2"],
            "n_tokens": [10, 15, 12],
        })
        
        entities_df = pd.DataFrame({
            "id": ["e1", "e2", "e3"],
            "text_unit_ids": [["tu1"], ["tu1", "tu2"], ["tu3"]],
        })
        
        relationships_df = pd.DataFrame({
            "id": ["r1", "r2"],
            "text_unit_ids": [["tu1", "tu2"], ["tu3"]],
        })
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        await self.table_provider.write_dataframe("relationships", relationships_df)
        
        # Execute streaming
        await create_final_text_units_streaming(
            self.table_provider, has_covariates=False
        )
        
        # Verify
        result = await self.table_provider.read_dataframe("text_units")
        assert len(result) == 3
        
        # Check tu1 has both entities and relationships
        tu1 = result[result["id"] == "tu1"].iloc[0]
        assert set(tu1["entity_ids"]) == {"e1", "e2"}
        assert set(tu1["relationship_ids"]) == {"r1"}
        assert len(tu1["covariate_ids"]) == 0
        
        # Check tu2
        tu2 = result[result["id"] == "tu2"].iloc[0]
        assert set(tu2["entity_ids"]) == {"e2"}
        assert set(tu2["relationship_ids"]) == {"r1"}
        
        # Check tu3
        tu3 = result[result["id"] == "tu3"].iloc[0]
        assert set(tu3["entity_ids"]) == {"e3"}
        assert set(tu3["relationship_ids"]) == {"r2"}

    async def test_create_final_text_units_streaming_with_covariates(self):
        """Test streaming with covariates included."""
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2"],
            "text": ["Text 1", "Text 2"],
            "document_id": ["doc1", "doc1"],
            "n_tokens": [10, 15],
        })
        
        entities_df = pd.DataFrame({
            "id": ["e1"],
            "text_unit_ids": [["tu1"]],
        })
        
        relationships_df = pd.DataFrame({
            "id": ["r1"],
            "text_unit_ids": [["tu1"]],
        })
        
        covariates_df = pd.DataFrame({
            "id": ["c1", "c2", "c3"],
            "text_unit_id": ["tu1", "tu1", "tu2"],
        })
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        await self.table_provider.write_dataframe("relationships", relationships_df)
        await self.table_provider.write_dataframe("covariates", covariates_df)
        
        # Execute with covariates
        await create_final_text_units_streaming(
            self.table_provider, has_covariates=True
        )
        
        # Verify
        result = await self.table_provider.read_dataframe("text_units")
        
        tu1 = result[result["id"] == "tu1"].iloc[0]
        assert set(tu1["covariate_ids"]) == {"c1", "c2"}
        
        tu2 = result[result["id"] == "tu2"].iloc[0]
        assert set(tu2["covariate_ids"]) == {"c3"}

    async def test_create_final_text_units_streaming_no_matches(self):
        """Test text units with no matching entities or relationships."""
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2"],
            "text": ["Text 1", "Text 2"],
            "document_id": ["doc1", "doc1"],
            "n_tokens": [10, 15],
        })
        
        # Empty entities and relationships
        entities_df = pd.DataFrame({
            "id": [],
            "text_unit_ids": [],
        })
        
        relationships_df = pd.DataFrame({
            "id": [],
            "text_unit_ids": [],
        })
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        await self.table_provider.write_dataframe("relationships", relationships_df)
        
        # Execute
        await create_final_text_units_streaming(
            self.table_provider, has_covariates=False
        )
        
        # Verify - should have empty lists for IDs
        result = await self.table_provider.read_dataframe("text_units")
        assert len(result) == 2
        assert len(result.iloc[0]["entity_ids"]) == 0
        assert len(result.iloc[0]["relationship_ids"]) == 0
        assert len(result.iloc[0]["covariate_ids"]) == 0

    async def test_create_final_text_units_streaming_large_dataset(self):
        """Test with larger dataset to verify streaming benefits."""
        # Create 1000 text units
        text_units_df = pd.DataFrame({
            "id": [f"tu{i}" for i in range(1000)],
            "text": [f"Text {i}" for i in range(1000)],
            "document_id": [f"doc{i % 10}" for i in range(1000)],
            "n_tokens": [10 + (i % 20) for i in range(1000)],
        })
        
        # Create entities that reference multiple text units
        entities_df = pd.DataFrame({
            "id": [f"e{i}" for i in range(100)],
            "text_unit_ids": [
                [f"tu{j}" for j in range(i * 10, min((i + 1) * 10, 1000))]
                for i in range(100)
            ],
        })
        
        relationships_df = pd.DataFrame({
            "id": [f"r{i}" for i in range(50)],
            "text_unit_ids": [
                [f"tu{j}" for j in range(i * 20, min((i + 1) * 20, 1000))]
                for i in range(50)
            ],
        })
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        await self.table_provider.write_dataframe("relationships", relationships_df)
        
        # Execute
        await create_final_text_units_streaming(
            self.table_provider, has_covariates=False
        )
        
        # Verify
        result = await self.table_provider.read_dataframe("text_units")
        assert len(result) == 1000
        
        # Spot check a few
        tu0 = result[result["id"] == "tu0"].iloc[0]
        assert len(tu0["entity_ids"]) > 0
        assert len(tu0["relationship_ids"]) > 0

    async def test_create_final_text_units_preserves_fields(self):
        """Test that all required fields are preserved."""
        text_units_df = pd.DataFrame({
            "id": ["tu1"],
            "text": ["Sample text"],
            "document_id": ["doc1"],
            "n_tokens": [42],
        })
        
        entities_df = pd.DataFrame({"id": [], "text_unit_ids": []})
        relationships_df = pd.DataFrame({"id": [], "text_unit_ids": []})
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        await self.table_provider.write_dataframe("relationships", relationships_df)
        
        # Execute
        await create_final_text_units_streaming(
            self.table_provider, has_covariates=False
        )
        
        # Verify all fields present
        result = await self.table_provider.read_dataframe("text_units")
        row = result.iloc[0]
        
        assert row["id"] == "tu1"
        assert row["text"] == "Sample text"
        assert row["document_id"] == "doc1"
        assert row["n_tokens"] == 42
        assert "human_readable_id" in row
        assert "entity_ids" in row
        assert "relationship_ids" in row
        assert "covariate_ids" in row

    async def test_create_final_text_units_human_readable_id(self):
        """Test that human_readable_id is assigned correctly."""
        text_units_df = pd.DataFrame({
            "id": ["tu_c", "tu_a", "tu_b"],  # Non-sequential IDs
            "text": ["Text 1", "Text 2", "Text 3"],
            "document_id": ["doc1", "doc1", "doc1"],
            "n_tokens": [10, 10, 10],
        })
        
        entities_df = pd.DataFrame({"id": [], "text_unit_ids": []})
        relationships_df = pd.DataFrame({"id": [], "text_unit_ids": []})
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        await self.table_provider.write_dataframe("relationships", relationships_df)
        
        # Execute
        await create_final_text_units_streaming(
            self.table_provider, has_covariates=False
        )
        
        # Verify human_readable_id is sequential
        result = await self.table_provider.read_dataframe("text_units")
        assert set(result["human_readable_id"].tolist()) == {0, 1, 2}


if __name__ == "__main__":
    unittest.main()
