# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing a factory and supported vector store types."""

from enum import Enum
from typing import Any, ClassVar

from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.cosmosdb import CosmosDBVectoreStore
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.vector_stores.local_vector_store import LocalVectorStore


class VectorStoreType(str, Enum):
    """The supported vector store types."""

    LanceDB = "lancedb"
    AzureAISearch = "azure_ai_search"
    CosmosDB = "cosmosdb"
    Local = "local"


class VectorStoreFactory:
    """A factory for vector stores.

    Includes a method for users to register a custom vector store implementation.
    """

    vector_store_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, vector_store_type: str, vector_store: type):
        """Register a custom vector store implementation."""
        cls.vector_store_types[vector_store_type] = vector_store

    @classmethod
    def create_vector_store(
        cls, vector_store_type: VectorStoreType | str, kwargs: dict
    ) -> BaseVectorStore:
        """Create or get a vector store from the provided type."""
        match vector_store_type:
            case VectorStoreType.LanceDB:
                return LanceDBVectorStore(**kwargs)
            case VectorStoreType.AzureAISearch:
                return AzureAISearchVectorStore(**kwargs)
            case VectorStoreType.CosmosDB:
                return CosmosDBVectoreStore(**kwargs)
            case VectorStoreType.Local:
                return LocalVectorStore(**kwargs)
            case _:
                if vector_store_type in cls.vector_store_types:
                    return cls.vector_store_types[vector_store_type](**kwargs)
                msg = f"Unknown vector store type: {vector_store_type}"
                raise ValueError(msg)

def get_vector_store(
    store_type: VectorStoreType,
    collection_name: str,
    **kwargs: Any,
) -> BaseVectorStore:
    """Get a vector store instance based on the store type."""
    store_map: ClassVar[dict[VectorStoreType, type[BaseVectorStore]]] = {
        VectorStoreType.LanceDB: LanceDBVectorStore,
        VectorStoreType.AzureAISearch: AzureAISearchVectorStore,
        VectorStoreType.CosmosDB: CosmosDBVectoreStore,
        VectorStoreType.Local: LocalVectorStore,
    }

    store_class = store_map.get(store_type)
    if store_class is None:
        msg = f"Unsupported vector store type: {store_type}"
        raise ValueError(msg)

    store = store_class(collection_name=collection_name)
    store.connect(**kwargs)
    return store
