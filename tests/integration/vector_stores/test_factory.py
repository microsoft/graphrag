# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""VectorStoreFactory Tests.

These tests will test the VectorStoreFactory class and the creation of each vector store type that is natively supported.
"""

import pytest
from graphrag_vectors import (
    VectorStore,
    VectorStoreFactory,
    VectorStoreType,
)
from graphrag_vectors.azure_ai_search import AzureAISearchVectorStore
from graphrag_vectors.cosmosdb import CosmosDBVectorStore
from graphrag_vectors.lancedb import LanceDBVectorStore

# register the defaults, since they are lazily registered
VectorStoreFactory().register(VectorStoreType.LanceDB, LanceDBVectorStore)
VectorStoreFactory().register(VectorStoreType.AzureAISearch, AzureAISearchVectorStore)
VectorStoreFactory().register(VectorStoreType.CosmosDB, CosmosDBVectorStore)


def test_create_lancedb_vector_store():
    kwargs = {
        "db_uri": "/tmp/lancedb",
    }
    vector_store = VectorStoreFactory().create(VectorStoreType.LanceDB, kwargs)
    assert isinstance(vector_store, LanceDBVectorStore)
    assert vector_store.index_name == "vector_index"


@pytest.mark.skip(reason="Azure AI Search requires credentials and setup")
def test_create_azure_ai_search_vector_store():
    kwargs = {
        "url": "https://test.search.windows.net",
        "api_key": "test_key",
        "index_name": "test_collection",
    }
    vector_store = VectorStoreFactory().create(
        VectorStoreType.AzureAISearch,
        kwargs,
    )
    assert isinstance(vector_store, AzureAISearchVectorStore)


@pytest.mark.skip(reason="CosmosDB requires credentials and setup")
def test_create_cosmosdb_vector_store():
    kwargs = {
        "connection_string": "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key==",
        "database_name": "test_db",
        "index_name": "test_collection",
    }

    vector_store = VectorStoreFactory().create(
        VectorStoreType.CosmosDB,
        kwargs,
    )

    assert isinstance(vector_store, CosmosDBVectorStore)


def test_register_and_create_custom_vector_store():
    """Test registering and creating a custom vector store type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the VectorStore interface
    custom_vector_store_class = MagicMock(spec=VectorStore)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    instance.initialized = True
    custom_vector_store_class.return_value = instance

    VectorStoreFactory().register(
        "custom", lambda **kwargs: custom_vector_store_class(**kwargs)
    )

    vector_store = VectorStoreFactory().create("custom", {})

    assert custom_vector_store_class.called
    assert vector_store is instance
    # Access the attribute we set on our mock
    assert vector_store.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered vector store types
    assert "custom" in VectorStoreFactory()


def test_create_unknown_vector_store():
    with pytest.raises(ValueError, match="Strategy 'unknown' is not registered\\."):
        VectorStoreFactory().create("unknown")


def test_is_supported_type():
    # Test built-in types
    assert VectorStoreType.LanceDB in VectorStoreFactory()
    assert VectorStoreType.AzureAISearch in VectorStoreFactory()
    assert VectorStoreType.CosmosDB in VectorStoreFactory()

    # Test unknown type
    assert "unknown" not in VectorStoreFactory()


def test_register_class_directly_works():
    """Test that registering a class directly works."""
    from graphrag_vectors import VectorStore

    class CustomVectorStore(VectorStore):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def connect(self, **kwargs):
            pass

        def create_index(self, **kwargs):
            pass

        def load_documents(self, documents):
            pass

        def similarity_search_by_vector(self, query_embedding, k=10, **kwargs):
            return []

        def similarity_search_by_text(self, text, text_embedder, k=10, **kwargs):
            return []

        def search_by_id(self, id):
            from graphrag_vectors import VectorStoreDocument

            return VectorStoreDocument(id=id, vector=None)

    # VectorStoreFactory() allows registering classes directly (no TypeError)
    VectorStoreFactory().register("custom_class", CustomVectorStore)

    # Verify it was registered
    assert "custom_class" in VectorStoreFactory()

    # Test creating an instance
    vector_store = VectorStoreFactory().create(
        "custom_class",
        {},
    )

    assert isinstance(vector_store, CustomVectorStore)
