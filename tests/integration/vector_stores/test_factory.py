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
    }
    vector_store = VectorStoreFactory.create_vector_store(
        vector_store_type=VectorStoreType.LanceDB.value,
        vector_store_schema_config=VectorStoreSchemaConfig(
            index_name="test_collection"
        ),
        kwargs=kwargs,
    )
    assert isinstance(vector_store, LanceDBVectorStore)
    assert vector_store.index_name == "test_collection"


@pytest.mark.skip(reason="Azure AI Search requires credentials and setup")
def test_create_azure_ai_search_vector_store():
    kwargs = {
        "url": "https://test.search.windows.net",
        "api_key": "test_key",
    }
    vector_store = VectorStoreFactory.create_vector_store(
        vector_store_type=VectorStoreType.AzureAISearch.value,
        vector_store_schema_config=VectorStoreSchemaConfig(
            index_name="test_collection"
        ),
        kwargs=kwargs,
    )
    assert isinstance(vector_store, AzureAISearchVectorStore)


@pytest.mark.skip(reason="CosmosDB requires credentials and setup")
def test_create_cosmosdb_vector_store():
    kwargs = {
        "connection_string": "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key==",
        "database_name": "test_db",
    }

    vector_store = VectorStoreFactory.create_vector_store(
        vector_store_type=VectorStoreType.CosmosDB.value,
        vector_store_schema_config=VectorStoreSchemaConfig(
            index_name="test_collection"
        ),
        kwargs=kwargs,
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

    vector_store = VectorStoreFactory.create_vector_store(
        vector_store_type="custom", vector_store_schema_config=VectorStoreSchemaConfig()
    )

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
        VectorStoreFactory.create_vector_store(
            vector_store_type="unknown",
            vector_store_schema_config=VectorStoreSchemaConfig(),
        )


def test_is_supported_type():
    # Test built-in types
    assert VectorStoreFactory.is_supported_type(VectorStoreType.LanceDB.value)
    assert VectorStoreFactory.is_supported_type(VectorStoreType.AzureAISearch.value)
    assert VectorStoreFactory.is_supported_type(VectorStoreType.CosmosDB.value)

    # Test unknown type
    assert not VectorStoreFactory.is_supported_type("unknown")


def test_register_class_directly_works():
    """Test that registering a class directly works (VectorStoreFactory allows this)."""
    from graphrag.vector_stores.base import BaseVectorStore

    class CustomVectorStore(BaseVectorStore):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

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

    # VectorStoreFactory allows registering classes directly (no TypeError)
    VectorStoreFactory.register("custom_class", CustomVectorStore)

    # Verify it was registered
    assert "custom_class" in VectorStoreFactory.get_vector_store_types()
    assert VectorStoreFactory.is_supported_type("custom_class")

    # Test creating an instance
    vector_store = VectorStoreFactory.create_vector_store(
        vector_store_type="custom_class",
        vector_store_schema_config=VectorStoreSchemaConfig(),
    )

    assert isinstance(vector_store, CustomVectorStore)
