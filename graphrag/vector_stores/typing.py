# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the supported vector store types."""

from enum import Enum
from typing import ClassVar

from .azure_ai_search import AzureAISearch
from .lancedb import LanceDBVectorStore
from .qdrant import QdrantVectorStore


class VectorStoreType(str, Enum):
    """The supported vector store types."""

    LanceDB = "lancedb"
    AzureAISearch = "azure_ai_search"
    Qdrant = "qdrant"


class VectorStoreFactory:
    """A factory class for creating vector stores."""

    vector_store_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, vector_store_type: str, vector_store: type):
        """Register a vector store type."""
        cls.vector_store_types[vector_store_type] = vector_store

    @classmethod
    def get_vector_store(
        cls, vector_store_type: VectorStoreType | str, kwargs: dict
    ) -> LanceDBVectorStore | AzureAISearch | QdrantVectorStore:
        """Get the vector store type from a string."""
        match vector_store_type:
            case VectorStoreType.LanceDB:
                return LanceDBVectorStore(**kwargs)
            case VectorStoreType.AzureAISearch:
                return AzureAISearch(**kwargs)
            case VectorStoreType.Qdrant:
                return QdrantVectorStore(**kwargs)
            case _:
                if vector_store_type in cls.vector_store_types:
                    return cls.vector_store_types[vector_store_type](**kwargs)
                msg = f"Unknown vector store type: {vector_store_type}"
                raise ValueError(msg)
