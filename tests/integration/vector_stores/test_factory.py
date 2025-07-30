# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""VectorStoreFactory Tests.

These tests will test the VectorStoreFactory class and the creation of each vector store type that is natively supported.
"""

import pytest

from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.cosmosdb import CosmosDBVectorStore
from graphrag.vector_stores.factory import VectorStoreFactory, VectorStoreType
from graphrag.vector_stores.lancedb import LanceDBVectorStore


def test_create_lancedb_vector_store():
    kwargs = {
        "collection_name": "test_collection",
        "db_uri": "/tmp/lancedb",
    }
    vector_store = VectorStoreFactory.create_vector_store(
        VectorStoreType.LanceDB, kwargs
    )
    assert isinstance(vector_store, LanceDBVectorStore)
    assert vector_store.collection_name == "test_collection"


@pytest.mark.skip(reason="Azure AI Search requires credentials and setup")
def test_create_azure_ai_search_vector_store():
    kwargs = {
        "collection_name": "test_collection",
        "url": "https://test.search.windows.net",
        "api_key": "test_key",
    }
    vector_store = VectorStoreFactory.create_vector_store(
        VectorStoreType.AzureAISearch, kwargs
    )
    assert isinstance(vector_store, AzureAISearchVectorStore)


@pytest.mark.skip(reason="CosmosDB requires credentials and setup")
def test_create_cosmosdb_vector_store():
    kwargs = {
        "collection_name": "test_collection",
        "connection_string": "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key==",
        "database_name": "test_db",
    }
    vector_store = VectorStoreFactory.create_vector_store(
        VectorStoreType.CosmosDB, kwargs
    )
    assert isinstance(vector_store, CosmosDBVectorStore)


def test_register_and_create_custom_vector_store():
    """Test registering and creating a custom vector store type."""
    from unittest.mock import MagicMock

    # Create a mock that satisfies the BaseVectorStore interface
    custom_vector_store_class = MagicMock(spec=BaseVectorStore)
    # Make the mock return a mock instance when instantiated
    instance = MagicMock()
    instance.initialized = True
    custom_vector_store_class.return_value = instance

    VectorStoreFactory.register(
        "custom", lambda **kwargs: custom_vector_store_class(**kwargs)
    )
    vector_store = VectorStoreFactory.create_vector_store("custom", {})

    assert custom_vector_store_class.called
    assert vector_store is instance
    # Access the attribute we set on our mock
    assert vector_store.initialized is True  # type: ignore # Attribute only exists on our mock

    # Check if it's in the list of registered vector store types
    assert "custom" in VectorStoreFactory.get_vector_store_types()
    assert VectorStoreFactory.is_supported_type("custom")


def test_get_vector_store_types():
    vector_store_types = VectorStoreFactory.get_vector_store_types()
    # Check that built-in types are registered
    assert VectorStoreType.LanceDB.value in vector_store_types
    assert VectorStoreType.AzureAISearch.value in vector_store_types
    assert VectorStoreType.CosmosDB.value in vector_store_types


def test_create_unknown_vector_store():
    with pytest.raises(ValueError, match="Unknown vector store type: unknown"):
        VectorStoreFactory.create_vector_store("unknown", {})


def test_is_supported_type():
    # Test built-in types
    assert VectorStoreFactory.is_supported_type(VectorStoreType.LanceDB.value)
    assert VectorStoreFactory.is_supported_type(VectorStoreType.AzureAISearch.value)
    assert VectorStoreFactory.is_supported_type(VectorStoreType.CosmosDB.value)

    # Test unknown type
    assert not VectorStoreFactory.is_supported_type("unknown")


def test_enum_and_string_compatibility():
    """Test that both enum and string types work for vector store creation."""
    kwargs = {
        "collection_name": "test_collection",
        "db_uri": "/tmp/lancedb",
    }

    # Test with enum
    vector_store_enum = VectorStoreFactory.create_vector_store(
        VectorStoreType.LanceDB, kwargs
    )
    assert isinstance(vector_store_enum, LanceDBVectorStore)

    # Test with string
    vector_store_str = VectorStoreFactory.create_vector_store("lancedb", kwargs)
    assert isinstance(vector_store_str, LanceDBVectorStore)

    # Both should create the same type
    assert type(vector_store_enum) is type(vector_store_str)


def test_register_class_directly_raises_error():
    """Test that registering a class directly raises a TypeError."""
    from graphrag.vector_stores.base import BaseVectorStore

    class CustomVectorStore(BaseVectorStore):
        def __init__(self, **kwargs):
            super().__init__(collection_name="test", **kwargs)

        def connect(self, **kwargs):
            pass

        def load_documents(self, documents, overwrite=True):
            pass

        def similarity_search_by_vector(self, query_embedding, k=10, **kwargs):
            return []

        def similarity_search_by_text(self, text, text_embedder, k=10, **kwargs):
            return []

        def filter_by_id(self, include_ids):
            return {}

        def search_by_id(self, id):
            from graphrag.vector_stores.base import VectorStoreDocument

            return VectorStoreDocument(id=id, text="test", vector=None)

    # Attempting to register a class directly should raise TypeError
    with pytest.raises(
        TypeError, match="Registering classes directly is no longer supported"
    ):
        VectorStoreFactory.register("custom_class", CustomVectorStore)
