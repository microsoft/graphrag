# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating a vector store."""

from __future__ import annotations

from graphrag_factory import Factory

from graphrag.config.enums import VectorStoreType
from graphrag.vector_stores.azure_ai_search import AzureAISearchVectorStore
from graphrag.vector_stores.base import BaseVectorStore
from graphrag.vector_stores.cosmosdb import CosmosDBVectorStore
from graphrag.vector_stores.lancedb import LanceDBVectorStore


class VectorStoreFactory(Factory[BaseVectorStore]):
    """A factory for vector stores.

    Includes a method for users to register a custom vector store implementation.

    Configuration arguments are passed to each vector store implementation as kwargs
    for individual enforcement of required/optional arguments.
    """


# --- register built-in vector store implementations ---
vector_store_factory = VectorStoreFactory()
vector_store_factory.register(VectorStoreType.LanceDB.value, LanceDBVectorStore)
vector_store_factory.register(
    VectorStoreType.AzureAISearch.value, AzureAISearchVectorStore
)
vector_store_factory.register(VectorStoreType.CosmosDB.value, CosmosDBVectorStore)
