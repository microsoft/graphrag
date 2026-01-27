# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Vector store type enum."""

from enum import StrEnum


class VectorStoreType(StrEnum):
    """The supported vector store types."""

    LanceDB = "lancedb"
    AzureAISearch = "azure_ai_search"
    CosmosDB = "cosmosdb"
