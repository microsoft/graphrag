# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for Azure AI Search vector store implementation."""

import os
from unittest.mock import MagicMock, patch

import pytest

from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
from graphrag.vector_stores.base import VectorStoreDocument

TEST_AZURE_AI_SEARCH_URL = os.environ.get(
    "TEST_AZURE_AI_SEARCH_URL", "https://test-url.search.windows.net"
)
TEST_AZURE_AI_SEARCH_KEY = os.environ.get("TEST_AZURE_AI_SEARCH_KEY", "test_api_key")


class TestAzureAISearchVectorStore:
    """Test class for AzureAISearchVectorStore."""

    @pytest.fixture
    def mock_search_client(self):
        """Create a mock Azure AI Search client."""
        with patch(
            "graphrag.vector_stores.azure_ai_search.SearchClient"
        ) as mock_client:
            yield mock_client.return_value

    @pytest.fixture
    def mock_index_client(self):
        """Create a mock Azure AI Search index client."""
        with patch(
            "graphrag.vector_stores.azure_ai_search.SearchIndexClient"
        ) as mock_client:
            yield mock_client.return_value

    @pytest.fixture
    def vector_store(self, mock_search_client, mock_index_client):
        """Create an Azure AI Search vector store instance."""
        vector_store = AzureAISearchVectorStore(collection_name="test_vectors")

        # Create the necessary mocks first
        vector_store.db_connection = mock_search_client
        vector_store.index_client = mock_index_client

        vector_store.connect(
            url=TEST_AZURE_AI_SEARCH_URL,
            api_key=TEST_AZURE_AI_SEARCH_KEY,
            vector_size=5,
        )
        return vector_store

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            VectorStoreDocument(
                id="doc1",
                text="This is document 1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                attributes={"title": "Doc 1", "category": "test"},
            ),
            VectorStoreDocument(
                id="doc2",
                text="This is document 2",
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
                attributes={"title": "Doc 2", "category": "test"},
            ),
        ]

    async def test_vector_store_operations(
        self, vector_store, sample_documents, mock_search_client, mock_index_client
    ):
        """Test basic vector store operations with Azure AI Search."""
        # Setup mock responses
        mock_index_client.list_index_names.return_value = []
        mock_index_client.create_or_update_index = MagicMock()
        mock_search_client.upload_documents = MagicMock()

        search_results = [
            {
                "id": "doc1",
                "text": "This is document 1",
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
                "attributes": '{"title": "Doc 1", "category": "test"}',
                "@search.score": 0.9,
            },
            {
                "id": "doc2",
                "text": "This is document 2",
                "vector": [0.2, 0.3, 0.4, 0.5, 0.6],
                "attributes": '{"title": "Doc 2", "category": "test"}',
                "@search.score": 0.8,
            },
        ]
        mock_search_client.search.return_value = search_results

        mock_search_client.get_document.return_value = {
            "id": "doc1",
            "text": "This is document 1",
            "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
            "attributes": '{"title": "Doc 1", "category": "test"}',
        }

        vector_store.load_documents(sample_documents)
        assert mock_index_client.create_or_update_index.called
        assert mock_search_client.upload_documents.called

        filter_query = vector_store.filter_by_id(["doc1", "doc2"])
        assert filter_query == "search.in(id, 'doc1,doc2', ',')"

        vector_results = vector_store.similarity_search_by_vector(
            [0.1, 0.2, 0.3, 0.4, 0.5], k=2
        )
        assert len(vector_results) == 2
        assert vector_results[0].document.id == "doc1"
        assert vector_results[0].score == 0.9

        # Define a simple text embedder function for testing
        def mock_embedder(text: str) -> list[float]:
            return [0.1, 0.2, 0.3, 0.4, 0.5]

        text_results = vector_store.similarity_search_by_text(
            "test query", mock_embedder, k=2
        )
        assert len(text_results) == 2

        doc = vector_store.search_by_id("doc1")
        assert doc.id == "doc1"
        assert doc.text == "This is document 1"
        assert doc.attributes["title"] == "Doc 1"

    async def test_empty_embedding(self, vector_store, mock_search_client):
        """Test similarity search by text with empty embedding."""

        # Create a mock embedder that returns None and verify that no results are produced
        def none_embedder(text: str) -> None:
            return None

        results = vector_store.similarity_search_by_text(
            "test query", none_embedder, k=1
        )
        assert not mock_search_client.search.called
        assert len(results) == 0
