# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating a vector store."""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphrag_common.factory import Factory, ServiceScope

from graphrag_vectors.vector_store import VectorStore
from graphrag_vectors.vector_store_type import VectorStoreType

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphrag_vectors.index_schema import IndexSchema
    from graphrag_vectors.vector_store_config import VectorStoreConfig


class VectorStoreFactory(Factory[VectorStore]):
    """A factory for vector stores.

    Includes a method for users to register a custom vector store implementation.

    Configuration arguments are passed to each vector store implementation as kwargs
    for individual enforcement of required/optional arguments.
    """


vector_store_factory = VectorStoreFactory()


def register_vector_store(
    vector_store_type: str,
    vector_store_initializer: Callable[..., VectorStore],
    scope: ServiceScope = "transient",
) -> None:
    """Register a custom vector store implementation.

    Args
    ----
        - vector_store_type: str
            The vector store id to register.
        - vector_store_initializer: Callable[..., VectorStore]
            The vector store initializer to register.
        - scope: ServiceScope
            The service scope for the vector store (default: "transient").
    """
    vector_store_factory.register(vector_store_type, vector_store_initializer, scope)


def create_vector_store(
    config: VectorStoreConfig, index_schema: IndexSchema
) -> VectorStore:
    """Create a vector store implementation based on the given type and configuration.

    Args
    ----
        - config: VectorStoreConfig
            The base vector store configuration.
        - index_schema: IndexSchema
            The index schema configuration for the vector store instance - i.e., for the specific table we are reading/writing.

    Returns
    -------
        VectorStore
            The created vector store implementation.
    """
    strategy = config.type

    # Lazy load built-in implementations
    if strategy not in vector_store_factory:
        match strategy:
            case VectorStoreType.LanceDB:
                from graphrag_vectors.lancedb import LanceDBVectorStore

                register_vector_store(VectorStoreType.LanceDB, LanceDBVectorStore)
            case VectorStoreType.AzureAISearch:
                from graphrag_vectors.azure_ai_search import AzureAISearchVectorStore

                register_vector_store(
                    VectorStoreType.AzureAISearch, AzureAISearchVectorStore
                )
            case VectorStoreType.CosmosDB:
                from graphrag_vectors.cosmosdb import CosmosDBVectorStore

                register_vector_store(VectorStoreType.CosmosDB, CosmosDBVectorStore)
            case _:
                msg = f"Vector store type '{strategy}' is not registered in the VectorStoreFactory. Registered types: {', '.join(vector_store_factory.keys())}."
                raise ValueError(msg)

    # collapse the base config and specific index config into a single dict for the initializer
    config_model = config.model_dump()
    index_model = index_schema.model_dump()
    return vector_store_factory.create(
        strategy, init_args={**config_model, **index_model}
    )
