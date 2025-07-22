# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing a factory and supported vector store types."""

from __future__ import annotations

from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphrag.vector_stores.base import BaseVectorStore


class VectorStoreType(str, Enum):
    """The supported vector store types."""

    LanceDB = "lancedb"
    AzureAISearch = "azure_ai_search"
    CosmosDB = "cosmosdb"


class VectorStoreFactory:
    """A factory for vector stores.

    Includes a method for users to register a custom vector store implementation.

    Configuration arguments are passed to each vector store implementation as kwargs
    for individual enforcement of required/optional arguments.
    """

    _vector_store_registry: ClassVar[dict[str, Callable[..., BaseVectorStore]]] = {}
    vector_store_types: ClassVar[dict[str, type]] = {}  # For backward compatibility

    @classmethod
    def register(
        cls, vector_store_type: str, creator: Callable[..., BaseVectorStore] | type
    ) -> None:
        """Register a custom vector store implementation.

        Args:
            vector_store_type: The type identifier for the vector store.
            creator: A callable that creates an instance of the vector store,
                    or a class type for backward compatibility.
        """
        # Handle backward compatibility for direct class types
        if isinstance(creator, type) or (hasattr(creator, "__name__") and callable(creator) and not hasattr(creator, "__annotations__")):
            # Create a wrapper function for the class
            def class_creator(**kwargs) -> BaseVectorStore:
                return creator(**kwargs)
            cls._vector_store_registry[vector_store_type] = class_creator
            cls.vector_store_types[vector_store_type] = creator
        else:
            cls._vector_store_registry[vector_store_type] = creator
            # For backward compatibility with code that may access vector_store_types directly
            if (
                callable(creator)
                and hasattr(creator, "__annotations__")
                and "return" in creator.__annotations__
            ):
                with suppress(TypeError, KeyError):
                    cls.vector_store_types[vector_store_type] = creator.__annotations__["return"]

    @classmethod
    def create_vector_store(
        cls, vector_store_type: VectorStoreType | str, kwargs: dict
    ) -> BaseVectorStore:
        """Create a vector store object from the provided type.

        Args:
            vector_store_type: The type of vector store to create.
            kwargs: Additional keyword arguments for the vector store constructor.

        Returns
        -------
            A BaseVectorStore instance.

        Raises
        ------
            ValueError: If the vector store type is not registered.
        """
        vector_store_type_str = (
            vector_store_type.value
            if isinstance(vector_store_type, VectorStoreType)
            else vector_store_type
        )

        if vector_store_type_str not in cls._vector_store_registry:
            msg = f"Unknown vector store type: {vector_store_type}"
            raise ValueError(msg)

        return cls._vector_store_registry[vector_store_type_str](**kwargs)

    @classmethod
    def get_vector_store_types(cls) -> list[str]:
        """Get the registered vector store implementations."""
        return list(cls._vector_store_registry.keys())

    @classmethod
    def is_supported_vector_store_type(cls, vector_store_type: str) -> bool:
        """Check if the given vector store type is supported."""
        return vector_store_type in cls._vector_store_registry


# --- Factory functions for built-in vector stores ---


def create_lancedb_vector_store(**kwargs) -> BaseVectorStore:
    """Create a LanceDB vector store."""
    from graphrag.vector_stores.lancedb import LanceDBVectorStore
    return LanceDBVectorStore(**kwargs)


def create_azure_ai_search_vector_store(**kwargs) -> BaseVectorStore:
    """Create an Azure AI Search vector store."""
    from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
    return AzureAISearchVectorStore(**kwargs)


def create_cosmosdb_vector_store(**kwargs) -> BaseVectorStore:
    """Create a CosmosDB vector store."""
    from graphrag.vector_stores.cosmosdb import CosmosDBVectorStore
    return CosmosDBVectorStore(**kwargs)


# --- Register default implementations ---
VectorStoreFactory.register(VectorStoreType.LanceDB.value, create_lancedb_vector_store)
VectorStoreFactory.register(VectorStoreType.AzureAISearch.value, create_azure_ai_search_vector_store)
VectorStoreFactory.register(VectorStoreType.CosmosDB.value, create_cosmosdb_vector_store)
