# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for LanceDB vector store implementation."""

import shutil
import tempfile

import numpy as np
import pytest

from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.vector_stores.base import VectorStoreDocument
from graphrag.vector_stores.lancedb import LanceDBVectorStore


class TestLanceDBVectorStore:
    """Test class for TestLanceDBVectorStore."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            VectorStoreDocument(
                id="1",
                text="This is document 1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                attributes={"title": "Doc 1", "category": "test"},
            ),
            VectorStoreDocument(
                id="2",
                text="This is document 2",
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
                attributes={"title": "Doc 2", "category": "test"},
            ),
            VectorStoreDocument(
                id="3",
                text="This is document 3",
                vector=[0.3, 0.4, 0.5, 0.6, 0.7],
                attributes={"title": "Doc 3", "category": "test"},
            ),
        ]

    @pytest.fixture
    def sample_documents_categories(self):
        """Create sample documents with different categories for testing."""
        return [
            VectorStoreDocument(
                id="1",
                text="Document about cats",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                attributes={"category": "animals"},
            ),
            VectorStoreDocument(
                id="2",
                text="Document about dogs",
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
                attributes={"category": "animals"},
            ),
            VectorStoreDocument(
                id="3",
                text="Document about cars",
                vector=[0.3, 0.4, 0.5, 0.6, 0.7],
                attributes={"category": "vehicles"},
            ),
        ]

    def test_vector_store_operations(self, sample_documents):
        """Test basic vector store operations with LanceDB."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                vector_store_schema_config=VectorStoreSchemaConfig(
                    index_name="test_collection", vector_size=5
                )
            )
            vector_store.connect(db_uri=temp_dir)
            vector_store.load_documents(sample_documents[:2])

            if vector_store.index_name:
                assert (
                    vector_store.index_name in vector_store.db_connection.table_names()
                )

            doc = vector_store.search_by_id("1")
            assert doc.id == "1"
            assert doc.text == "This is document 1"

            assert doc.vector is not None
            assert np.allclose(doc.vector, [0.1, 0.2, 0.3, 0.4, 0.5])
            assert doc.attributes["title"] == "Doc 1"

            filter_query = vector_store.filter_by_id(["1"])
            assert filter_query == "id in ('1')"

            results = vector_store.similarity_search_by_vector(
                [0.1, 0.2, 0.3, 0.4, 0.5], k=2
            )
            assert 1 <= len(results) <= 2
            assert isinstance(results[0].score, float)

            # Test append mode
            vector_store.load_documents([sample_documents[2]], overwrite=False)
            result = vector_store.search_by_id("3")
            assert result.id == "3"
            assert result.text == "This is document 3"

            # Define a simple text embedder function for testing
            def mock_embedder(text: str) -> list[float]:
                return [0.1, 0.2, 0.3, 0.4, 0.5]

            text_results = vector_store.similarity_search_by_text(
                "test query", mock_embedder, k=2
            )
            assert 1 <= len(text_results) <= 2
            assert isinstance(text_results[0].score, float)

            # Test non-existent document
            non_existent = vector_store.search_by_id("nonexistent")
            assert non_existent.id == "nonexistent"
            assert non_existent.text is None
            assert non_existent.vector is None
        finally:
            shutil.rmtree(temp_dir)

    def test_empty_collection(self):
        """Test creating an empty collection."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                vector_store_schema_config=VectorStoreSchemaConfig(
                    index_name="empty_collection", vector_size=5
                )
            )
            vector_store.connect(db_uri=temp_dir)

            # Load the vector store with a document, then delete it
            sample_doc = VectorStoreDocument(
                id="tmp",
                text="Temporary document to create schema",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                attributes={"title": "Tmp"},
            )
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
                text="This is document 1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                attributes={"title": "Doc 1"},
            )
            vector_store.load_documents([doc], overwrite=False)

            result = vector_store.search_by_id("1")
            assert result.id == "1"
            assert result.text == "This is document 1"
        finally:
            # Clean up - remove the temporary directory
            shutil.rmtree(temp_dir)

    def test_filter_search(self, sample_documents_categories):
        """Test filtered search with LanceDB."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                vector_store_schema_config=VectorStoreSchemaConfig(
                    index_name="filter_collection", vector_size=5
                )
            )

            vector_store.connect(db_uri=temp_dir)

            vector_store.load_documents(sample_documents_categories)

            # Filter to include only documents about animals
            vector_store.filter_by_id(["1", "2"])
            results = vector_store.similarity_search_by_vector(
                [0.1, 0.2, 0.3, 0.4, 0.5], k=3
            )

            # Should return at most 2 documents (the filtered ones)
            assert len(results) <= 2
            ids = [result.document.id for result in results]
            assert "3" not in ids
            assert set(ids).issubset({"1", "2"})
        finally:
            shutil.rmtree(temp_dir)

    def test_vector_store_customization(self, sample_documents):
        """Test vector store customization with LanceDB."""
        # Create a temporary directory for the test database
        temp_dir = tempfile.mkdtemp()
        try:
            vector_store = LanceDBVectorStore(
                vector_store_schema_config=VectorStoreSchemaConfig(
                    index_name="text-embeddings",
                    id_field="id_custom",
                    text_field="text_custom",
                    vector_field="vector_custom",
                    attributes_field="attributes_custom",
                    vector_size=5,
                ),
            )
            vector_store.connect(db_uri=temp_dir)
            vector_store.load_documents(sample_documents[:2])

            if vector_store.index_name:
                assert (
                    vector_store.index_name in vector_store.db_connection.table_names()
                )

            doc = vector_store.search_by_id("1")
            assert doc.id == "1"
            assert doc.text == "This is document 1"

            assert doc.vector is not None
            assert np.allclose(doc.vector, [0.1, 0.2, 0.3, 0.4, 0.5])
            assert doc.attributes["title"] == "Doc 1"

            filter_query = vector_store.filter_by_id(["1"])
            assert filter_query == f"{vector_store.id_field} in ('1')"

            results = vector_store.similarity_search_by_vector(
                [0.1, 0.2, 0.3, 0.4, 0.5], k=2
            )
            assert 1 <= len(results) <= 2
            assert isinstance(results[0].score, float)

            # Test append mode
            vector_store.load_documents([sample_documents[2]], overwrite=False)
            result = vector_store.search_by_id("3")
            assert result.id == "3"
            assert result.text == "This is document 3"

            # Define a simple text embedder function for testing
            def mock_embedder(text: str) -> list[float]:
                return [0.1, 0.2, 0.3, 0.4, 0.5]

            text_results = vector_store.similarity_search_by_text(
                "test query", mock_embedder, k=2
            )
            assert 1 <= len(text_results) <= 2
            assert isinstance(text_results[0].score, float)

            # Test non-existent document
            non_existent = vector_store.search_by_id("nonexistent")
            assert non_existent.id == "nonexistent"
            assert non_existent.text is None
            assert non_existent.vector is None
        finally:
            shutil.rmtree(temp_dir)
