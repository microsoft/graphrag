# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for CosmosDB vector store implementation."""

import sys

import numpy as np
import pytest
from graphrag_vectors import (
    VectorStoreDocument,
)
from graphrag_vectors.cosmosdb import CosmosDBVectorStore

# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

# the cosmosdb emulator is only available on windows runners at this time
if not sys.platform.startswith("win"):
    pytest.skip(
        "encountered windows-only tests -- will skip for now", allow_module_level=True
    )


def test_vector_store_operations():
    """Test basic vector store operations with CosmosDB."""
    vector_store = CosmosDBVectorStore(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="test_db",
        index_name="testvector",
    )

    try:
        vector_store.connect()

        docs = [
            VectorStoreDocument(
                id="doc1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            ),
            VectorStoreDocument(
                id="doc2",
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
            ),
        ]

        vector_store.create_index()
        vector_store.load_documents(docs)

        doc = vector_store.search_by_id("doc1")
        assert doc.id == "doc1"
        assert doc.vector is not None
        assert np.allclose(doc.vector, [0.1, 0.2, 0.3, 0.4, 0.5])

        # Define a simple text embedder function for testing
        def mock_embedder(text: str) -> list[float]:
            return [0.1, 0.2, 0.3, 0.4, 0.5]  # Return fixed embedding

        vector_results = vector_store.similarity_search_by_vector(
            [0.1, 0.2, 0.3, 0.4, 0.5], k=2
        )
        assert len(vector_results) > 0

        text_results = vector_store.similarity_search_by_text(
            "test query", mock_embedder, k=2
        )
        assert len(text_results) > 0
    finally:
        vector_store.clear()


def test_clear():
    """Test clearing the vector store."""
    vector_store = CosmosDBVectorStore(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="testclear",
        index_name="testclear",
    )
    try:
        vector_store.connect()

        doc = VectorStoreDocument(
            id="test",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        )

        vector_store.create_index()
        vector_store.load_documents([doc])
        result = vector_store.search_by_id("test")
        assert result.id == "test"

        # Clear and verify document is removed
        vector_store.clear()
        assert vector_store._database_exists() is False  # noqa: SLF001
    finally:
        pass


def test_vector_store_customization():
    """Test vector store customization with CosmosDB."""
    vector_store = CosmosDBVectorStore(
        connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
        database_name="test_db",
        index_name="text-embeddings",
        id_field="id",
        vector_field="vector_custom",
        vector_size=5,
    )

    try:
        vector_store.connect()

        docs = [
            VectorStoreDocument(
                id="doc1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            ),
            VectorStoreDocument(
                id="doc2",
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
            ),
        ]

        vector_store.create_index()
        vector_store.load_documents(docs)

        doc = vector_store.search_by_id("doc1")
        assert doc.id == "doc1"
        assert doc.vector is not None
        assert np.allclose(doc.vector, [0.1, 0.2, 0.3, 0.4, 0.5])

        # Define a simple text embedder function for testing
        def mock_embedder(text: str) -> list[float]:
            return [0.1, 0.2, 0.3, 0.4, 0.5]  # Return fixed embedding

        vector_results = vector_store.similarity_search_by_vector(
            [0.1, 0.2, 0.3, 0.4, 0.5], k=2
        )
        assert len(vector_results) > 0

        text_results = vector_store.similarity_search_by_text(
            "test query", mock_embedder, k=2
        )
        assert len(text_results) > 0
    finally:
        vector_store.clear()
