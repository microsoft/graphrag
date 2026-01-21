# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for LanceDB vector store implementation."""

import shutil
import tempfile

import numpy as np
import pytest
from graphrag_vectors import (
    VectorStoreDocument,
)
from graphrag_vectors.lancedb import LanceDBVectorStore


class TestLanceDBVectorStore:
    """Test class for TestLanceDBVectorStore."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            VectorStoreDocument(
                id="1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                data={"category": "animal"},
            ),
            VectorStoreDocument(
                id="2",
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
                data={"category": "animal"},
            ),
            VectorStoreDocument(
                id="3",
                vector=[0.3, 0.4, 0.5, 0.6, 0.7],
                data={"category": "plant"},
            ),
        ]

    def test_vector_store_operations(self, sample_documents):
        """Test basic vector store operations with LanceDB."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                db_uri=temp_dir, index_name="test_collection", vector_size=5
            )
            vector_store.connect()
            vector_store.create_index()
            vector_store.load_documents(sample_documents[:2])

            if vector_store.index_name:
                assert (
                    vector_store.index_name in vector_store.db_connection.table_names()
                )

            doc = vector_store.search_by_id("1")
            assert doc.id == "1"
            assert doc.vector is not None
            assert np.allclose(doc.vector, [0.1, 0.2, 0.3, 0.4, 0.5])

            results = vector_store.similarity_search_by_vector(
                [0.1, 0.2, 0.3, 0.4, 0.5], k=2
            )
            assert 1 <= len(results) <= 2
            assert isinstance(results[0].score, float)

            # Test append mode
            vector_store.create_index()
            vector_store.load_documents([sample_documents[2]])
            result = vector_store.search_by_id("3")
            assert result.id == "3"

            # Define a simple text embedder function for testing
            def mock_embedder(text: str) -> list[float]:
                return [0.1, 0.2, 0.3, 0.4, 0.5]

            text_results = vector_store.similarity_search_by_text(
                "test query", mock_embedder, k=2
            )
            assert 1 <= len(text_results) <= 2
            assert isinstance(text_results[0].score, float)

            # Test non-existent document
            with pytest.raises(IndexError):
                vector_store.search_by_id("nonexistent")
        finally:
            shutil.rmtree(temp_dir)

    def test_empty_collection(self):
        """Test creating an empty collection."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                db_uri=temp_dir, index_name="empty_collection", vector_size=5
            )
            vector_store.connect()

            # Load the vector store with a document, then delete it
            sample_doc = VectorStoreDocument(
                id="tmp",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            )
            vector_store.create_index()
            vector_store.load_documents([sample_doc])
            vector_store.db_connection.open_table(
                vector_store.index_name if vector_store.index_name else ""
            ).delete("id = 'tmp'")

            # Should still have the collection
            if vector_store.index_name:
                assert (
                    vector_store.index_name in vector_store.db_connection.table_names()
                )

            # Add a document after creating an empty collection
            doc = VectorStoreDocument(
                id="1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            )
            vector_store.create_index()
            vector_store.load_documents([doc])

            result = vector_store.search_by_id("1")
            assert result.id == "1"
        finally:
            # Clean up - remove the temporary directory
            shutil.rmtree(temp_dir)

    def test_vector_store_customization(self, sample_documents):
        """Test vector store customization with LanceDB."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                db_uri=temp_dir,
                index_name="text-embeddings",
                id_field="id_custom",
                vector_field="vector_custom",
                vector_size=5,
                fields={"category": "string"},
            )
            vector_store.connect()
            vector_store.create_index()
            vector_store.load_documents(sample_documents[:2])

            if vector_store.index_name:
                assert (
                    vector_store.index_name in vector_store.db_connection.table_names()
                )

            doc = vector_store.search_by_id("1")
            assert doc.id == "1"
            assert doc.vector is not None
            assert np.allclose(doc.vector, [0.1, 0.2, 0.3, 0.4, 0.5])

            results = vector_store.similarity_search_by_vector(
                [0.1, 0.2, 0.3, 0.4, 0.5], k=2
            )
            assert 1 <= len(results) <= 2
            assert isinstance(results[0].score, float)

            # Test append mode
            vector_store.create_index()
            vector_store.load_documents([sample_documents[2]])
            result = vector_store.search_by_id("3")
            assert result.id == "3"
            assert result.data["category"] == "plant"
            
            # Define a simple text embedder function for testing
            def mock_embedder(text: str) -> list[float]:
                return [0.1, 0.2, 0.3, 0.4, 0.5]

            text_results = vector_store.similarity_search_by_text(
                "test query", mock_embedder, k=2
            )
            assert 1 <= len(text_results) <= 2
            assert isinstance(text_results[0].score, float)

            # Test non-existent document
            with pytest.raises(IndexError):
                vector_store.search_by_id("nonexistent")

        finally:
            shutil.rmtree(temp_dir)
