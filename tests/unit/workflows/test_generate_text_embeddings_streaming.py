# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Tests for generate_text_embeddings workflow with streaming support."""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from graphrag.index.workflows.generate_text_embeddings import (
    generate_text_embeddings_streaming,
)
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


class TestGenerateTextEmbeddingsStreaming(unittest.IsolatedAsyncioTestCase):
    """Test suite for streaming generate_text_embeddings workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = create_storage(StorageConfig(type=StorageType.Memory))
        self.table_provider = ParquetTableProvider(storage=self.storage)
        
        # Mock embedding model
        self.mock_model = MagicMock()
        self.mock_model.tokenizer = MagicMock()
        
        # Mock callbacks
        self.mock_callbacks = MagicMock()
        
        # Mock vector store config with proper index schema
        self.mock_vector_store_config = MagicMock()
        self.mock_vector_store_config.index_schema = {
            "text_unit_text": MagicMock(),
            "entity_description": MagicMock(),
            "community_full_content": MagicMock(),
        }

    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.storage.clear()

    @patch("graphrag.index.workflows.generate_text_embeddings.create_vector_store")
    @patch("graphrag.index.operations.embed_text.run_embed_text.run_embed_text")
    async def test_generate_embeddings_streaming_text_units(
        self, mock_run_embed, mock_create_vector_store
    ):
        """Test streaming embeddings for text units."""
        # Setup test data
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2", "tu3"],
            "text": ["Text 1", "Text 2", "Text 3"],
            "n_tokens": [10, 12, 11],
        })
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Mock embedding results - use side_effect to return correct number
        def mock_embed_side_effect(*args, **kwargs):
            result = MagicMock()
            texts = args[0] if args else []
            result.embeddings = [[0.1, 0.2]] * len(texts)
            return result
        
        mock_run_embed.side_effect = mock_embed_side_effect
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_create_vector_store.return_value = mock_vector_store
        
        # Execute streaming
        await generate_text_embeddings_streaming(
            table_provider=self.table_provider,
            callbacks=self.mock_callbacks,
            model=self.mock_model,
            tokenizer=self.mock_model.tokenizer,
            batch_size=2,
            batch_max_tokens=1000,
            num_threads=4,
            vector_store_config=self.mock_vector_store_config,
            embedded_fields=["text_unit_text"],
            write_snapshots=True,
        )
        
        # Verify vector store was created and used
        mock_create_vector_store.assert_called_once()
        mock_vector_store.connect.assert_called_once()
        mock_vector_store.create_index.assert_called_once()
        
        # Verify embeddings were generated (should be 2 batches: [2 items, 1 item])
        assert mock_run_embed.call_count == 2
        
        # Verify snapshot was written
        assert await self.table_provider.has_dataframe("embeddings.text_unit_text")
        result = await self.table_provider.read_dataframe("embeddings.text_unit_text")
        assert len(result) == 3

    @patch("graphrag.index.workflows.generate_text_embeddings.create_vector_store")
    @patch("graphrag.index.operations.embed_text.run_embed_text.run_embed_text")
    async def test_generate_embeddings_streaming_entities(
        self, mock_run_embed, mock_create_vector_store
    ):
        """Test streaming embeddings for entities."""
        # Setup test data
        entities_df = pd.DataFrame({
            "id": ["e1", "e2"],
            "title": ["Entity 1", "Entity 2"],
            "description": ["Description 1", "Description 2"],
        })
        await self.table_provider.write_dataframe("entities", entities_df)
        
        # Mock embedding results
        mock_result = MagicMock()
        mock_result.embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_run_embed.return_value = mock_result
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_create_vector_store.return_value = mock_vector_store
        
        # Execute streaming
        await generate_text_embeddings_streaming(
            table_provider=self.table_provider,
            callbacks=self.mock_callbacks,
            model=self.mock_model,
            tokenizer=self.mock_model.tokenizer,
            batch_size=5,
            batch_max_tokens=1000,
            num_threads=4,
            vector_store_config=self.mock_vector_store_config,
            embedded_fields=["entity_description"],
            write_snapshots=True,
        )
        
        # Verify embeddings were generated (single batch)
        mock_run_embed.assert_called_once()
        
        # Check that title:description was prepared correctly
        call_args = mock_run_embed.call_args
        texts = call_args[0][0]  # First positional argument
        assert texts[0] == "Entity 1:Description 1"
        assert texts[1] == "Entity 2:Description 2"
        
        # Verify snapshot
        result = await self.table_provider.read_dataframe("embeddings.entity_description")
        assert len(result) == 2

    @patch("graphrag.index.workflows.generate_text_embeddings.create_vector_store")
    @patch("graphrag.index.operations.embed_text.run_embed_text.run_embed_text")
    async def test_generate_embeddings_streaming_batching(
        self, mock_run_embed, mock_create_vector_store
    ):
        """Test that batching works correctly."""
        # Create 10 text units with batch_size=3 should create 4 batches
        text_units_df = pd.DataFrame({
            "id": [f"tu{i}" for i in range(10)],
            "text": [f"Text {i}" for i in range(10)],
            "n_tokens": [10] * 10,
        })
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Mock embedding results - use side_effect to return correct number
        def mock_embed_side_effect(*args, **kwargs):
            result = MagicMock()
            texts = args[0] if args else []
            result.embeddings = [[0.1, 0.2]] * len(texts)
            return result
        
        mock_run_embed.side_effect = mock_embed_side_effect
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_create_vector_store.return_value = mock_vector_store
        
        # Execute with batch_size=3
        await generate_text_embeddings_streaming(
            table_provider=self.table_provider,
            callbacks=self.mock_callbacks,
            model=self.mock_model,
            tokenizer=self.mock_model.tokenizer,
            batch_size=3,
            batch_max_tokens=1000,
            num_threads=4,
            vector_store_config=self.mock_vector_store_config,
            embedded_fields=["text_unit_text"],
            write_snapshots=False,
        )
        
        # Verify batching: 10 items / 3 = 4 batches (3, 3, 3, 1)
        assert mock_run_embed.call_count == 4
        
        # Check batch sizes
        call_args_list = mock_run_embed.call_args_list
        assert len(call_args_list[0][0][0]) == 3  # First batch: 3 items
        assert len(call_args_list[1][0][0]) == 3  # Second batch: 3 items
        assert len(call_args_list[2][0][0]) == 3  # Third batch: 3 items
        assert len(call_args_list[3][0][0]) == 1  # Fourth batch: 1 item

    @patch("graphrag.index.workflows.generate_text_embeddings.create_vector_store")
    async def test_generate_embeddings_streaming_missing_table(
        self, mock_create_vector_store
    ):
        """Test handling of missing tables."""
        # Don't create any tables
        
        # Execute - should not raise error, just log warning
        await generate_text_embeddings_streaming(
            table_provider=self.table_provider,
            callbacks=self.mock_callbacks,
            model=self.mock_model,
            tokenizer=self.mock_model.tokenizer,
            batch_size=10,
            batch_max_tokens=1000,
            num_threads=4,
            vector_store_config=self.mock_vector_store_config,
            embedded_fields=["text_unit_text", "entity_description"],
            write_snapshots=False,
        )
        
        # Vector store should not have been created since no tables exist
        mock_create_vector_store.assert_not_called()

    @patch("graphrag.index.workflows.generate_text_embeddings.create_vector_store")
    @patch("graphrag.index.operations.embed_text.run_embed_text.run_embed_text")
    async def test_generate_embeddings_streaming_no_snapshot_write(
        self, mock_run_embed, mock_create_vector_store
    ):
        """Test that snapshots are not written when disabled."""
        # Setup test data
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2"],
            "text": ["Text 1", "Text 2"],
            "n_tokens": [10, 12],
        })
        await self.table_provider.write_dataframe("text_units", text_units_df)
        
        # Mock embedding results
        mock_result = MagicMock()
        mock_result.embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_run_embed.return_value = mock_result
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_create_vector_store.return_value = mock_vector_store
        
        # Execute with write_snapshots=False
        await generate_text_embeddings_streaming(
            table_provider=self.table_provider,
            callbacks=self.mock_callbacks,
            model=self.mock_model,
            tokenizer=self.mock_model.tokenizer,
            batch_size=10,
            batch_max_tokens=1000,
            num_threads=4,
            vector_store_config=self.mock_vector_store_config,
            embedded_fields=["text_unit_text"],
            write_snapshots=False,
        )
        
        # Verify snapshot table was not created
        assert not await self.table_provider.has_dataframe("embeddings.text_unit_text")

    @patch("graphrag.index.workflows.generate_text_embeddings.create_vector_store")
    @patch("graphrag.index.operations.embed_text.run_embed_text.run_embed_text")
    async def test_generate_embeddings_streaming_multiple_fields(
        self, mock_run_embed, mock_create_vector_store
    ):
        """Test processing multiple embedding fields."""
        # Setup test data
        text_units_df = pd.DataFrame({
            "id": ["tu1", "tu2"],
            "text": ["Text 1", "Text 2"],
            "n_tokens": [10, 12],
        })
        entities_df = pd.DataFrame({
            "id": ["e1"],
            "title": ["Entity 1"],
            "description": ["Description 1"],
        })
        
        await self.table_provider.write_dataframe("text_units", text_units_df)
        await self.table_provider.write_dataframe("entities", entities_df)
        
        # Mock embedding results - need to match the batch size being called
        mock_result = MagicMock()
        
        # Return embeddings matching the batch size
        def mock_embed_side_effect(*args, **kwargs):
            result = MagicMock()
            texts = args[0] if args else []
            result.embeddings = [[0.1, 0.2]] * len(texts)
            return result
        
        mock_run_embed.side_effect = mock_embed_side_effect
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_create_vector_store.return_value = mock_vector_store
        
        # Execute with both fields
        await generate_text_embeddings_streaming(
            table_provider=self.table_provider,
            callbacks=self.mock_callbacks,
            model=self.mock_model,
            tokenizer=self.mock_model.tokenizer,
            batch_size=10,
            batch_max_tokens=1000,
            num_threads=4,
            vector_store_config=self.mock_vector_store_config,
            embedded_fields=["text_unit_text", "entity_description"],
            write_snapshots=True,
        )
        
        # Verify both vector stores were created
        assert mock_create_vector_store.call_count == 2
        
        # Verify both snapshots exist
        assert await self.table_provider.has_dataframe("embeddings.text_unit_text")
        assert await self.table_provider.has_dataframe("embeddings.entity_description")


if __name__ == "__main__":
    unittest.main()
