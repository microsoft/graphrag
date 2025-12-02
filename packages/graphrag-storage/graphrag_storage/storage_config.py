# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Storage configuration model."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_storage.storage_type import StorageType


class StorageConfig(BaseModel):
    """The default configuration section for storage."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom storage implementations."""

    type: str = Field(
        description="The storage type to use. Builtin types include 'file', 'azure_blob', and 'azure_cosmos'.",
        default=StorageType.FILE,
    )

    encoding: str | None = Field(
        description="The encoding to use for file storage.",
        default=None,
    )

    base_dir: str | None = Field(
        description="The base directory for the output when using file or azure_blob storage.",
        default=None,
    )

    azure_connection_string: str | None = Field(
        description="The connection string for Azure Blob Storage or Azure CosmosDB.",
        default=None,
    )

    azure_container_name: str | None = Field(
        description="The Azure Blob Storage container name or CosmosDB container name to use.",
        default=None,
    )
    azure_storage_account_blob_url: str | None = Field(
        description="The Azure Blob Storage account blob url to use.",
        default=None,
    )
    azure_cosmosdb_database_name: str | None = Field(
        description="The Azure CosmosDB database name to use.",
        default=None,
    )
    azure_cosmosdb_account_url: str | None = Field(
        description="The Azure CosmosDB account url to use.",
        default=None,
    )
