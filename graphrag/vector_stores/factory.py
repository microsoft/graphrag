# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating a vector store."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from graphrag.config.enums import VectorStoreType
from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
from graphrag.vector_stores.cosmosdb import CosmosDBVectorStore
from graphrag.vector_stores.lancedb import LanceDBVectorStore

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphrag.config.models.vector_store_schema_config import (
        VectorStoreSchemaConfig,
    )
    from graphrag.vector_stores.base import BaseVectorStore


class VectorStoreFactory:
    """A factory for vector stores.

    Includes a method for users to register a custom vector store implementation.

    Configuration arguments are passed to each vector store implementation as kwargs
    for individual enforcement of required/optional arguments.
    """

    _registry: ClassVar[dict[str, Callable[..., BaseVectorStore]]] = {}

    @classmethod
    def register(
        cls, vector_store_type: str, creator: Callable[..., BaseVectorStore]
    ) -> None:
        """Register a custom vector store implementation.

        Args:
            vector_store_type: The type identifier for the vector store.
            creator: A class or callable that creates an instance of BaseVectorStore.

        Raises
        ------
            TypeError: If creator is a class type instead of a factory function.
        """
        cls._registry[vector_store_type] = creator

    @classmethod
    def create_vector_store(
        cls,
        vector_store_type: str,
        vector_store_schema_config: VectorStoreSchemaConfig,
        **kwargs: dict,
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
        if vector_store_type not in cls._registry:
            msg = f"Unknown vector store type: {vector_store_type}"
            raise ValueError(msg)

        return cls._registry[vector_store_type](
            vector_store_schema_config=vector_store_schema_config, **kwargs
        )

    @classmethod
    def get_vector_store_types(cls) -> list[str]:
        """Get the registered vector store implementations."""
        return list(cls._registry.keys())

    @classmethod
    def is_supported_type(cls, vector_store_type: str) -> bool:
        """Check if the given vector store type is supported."""
        return vector_store_type in cls._registry


# --- register built-in vector store implementations ---
VectorStoreFactory.register(VectorStoreType.LanceDB.value, LanceDBVectorStore)
VectorStoreFactory.register(
    VectorStoreType.AzureAISearch.value, AzureAISearchVectorStore
)
VectorStoreFactory.register(VectorStoreType.CosmosDB.value, CosmosDBVectorStore)
