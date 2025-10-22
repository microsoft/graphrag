# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""VectorStoreFactory Tests.

These tests will test the VectorStoreFactory class and the creation of each vector store type that is natively supported.
"""

import pytest
from graphrag.config.enums import VectorStoreType
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.cosmosdb import CosmosDBVectorStore
from graphrag.vector_stores.factory import VectorStoreFactory
from graphrag.vector_stores.lancedb import LanceDBVectorStore


def test_create_lancedb_vector_store():
    kwargs = {
        "db_uri": "/tmp/lancedb",
        "vector_store_schema_config": VectorStoreSchemaConfig(
            index_name="test_collection"
        ),
    }
    vector_store = VectorStoreFactory().create(
        VectorStoreType.LanceDB.value,
        kwargs,
    )
    assert isinstance(vector_store, LanceDBVectorStore)
    assert vector_store.index_name == "test_collection"


@pytest.mark.skip(reason="Azure AI Search requires credentials and setup")
def test_create_azure_ai_search_vector_store():
    kwargs = {
        "url": "https://test.search.windows.net",
        "api_key": "test_key",
        "vector_store_schema_config": VectorStoreSchemaConfig(
            index_name="test_collection"
        ),
    }
    vector_store = VectorStoreFactory().create(
        VectorStoreType.AzureAISearch.value,
        kwargs,
    )
    assert isinstance(vector_store, AzureAISearchVectorStore)


@pytest.mark.skip(reason="CosmosDB requires credentials and setup")
def test_create_cosmosdb_vector_store():
    kwargs = {
        "connection_string": "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key==",
        "database_name": "test_db",
        "vector_store_schema_config": VectorStoreSchemaConfig(
            index_name="test_collection"
        ),
    }

    vector_store = VectorStoreFactory().create(
        VectorStoreType.CosmosDB.value,
        kwargs,
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

    VectorStoreFactory().register(
        "custom", lambda **kwargs: custom_vector_store_class(**kwargs)
    )

    vector_store = VectorStoreFactory().create(
        "custom", {"vector_store_schema_config": VectorStoreSchemaConfig()}
    )

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
    assert VectorStoreType.LanceDB.value in VectorStoreFactory()
    assert VectorStoreType.AzureAISearch.value in VectorStoreFactory()
    assert VectorStoreType.CosmosDB.value in VectorStoreFactory()

    # Test unknown type
    assert "unknown" not in VectorStoreFactory()


def test_register_class_directly_works():
    """Test that registering a class directly works."""
    from graphrag.vector_stores.base import BaseVectorStore

    class CustomVectorStore(BaseVectorStore):
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
            from graphrag.vector_stores.base import VectorStoreDocument

            return VectorStoreDocument(id=id, vector=None)

    # VectorStoreFactory() allows registering classes directly (no TypeError)
    VectorStoreFactory().register("custom_class", CustomVectorStore)

    # Verify it was registered
    assert "custom_class" in VectorStoreFactory()

    # Test creating an instance
    vector_store = VectorStoreFactory().create(
        "custom_class",
        {"vector_store_schema_config": VectorStoreSchemaConfig()},
    )

    assert isinstance(vector_store, CustomVectorStore)
