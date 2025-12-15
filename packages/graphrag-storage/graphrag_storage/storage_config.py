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
        description="The storage type to use. Builtin types include 'File', 'AzureBlob', and 'AzureCosmos'.",
        default=StorageType.File,
    )

    encoding: str | None = Field(
        description="The encoding to use for file storage.",
        default=None,
    )

    base_dir: str | None = Field(
        description="The base directory for the output when using file or AzureBlob storage.",
        default=None,
    )

    connection_string: str | None = Field(
        description="The connection string for remote services.",
        default=None,
    )

    container_name: str | None = Field(
        description="The Azure Blob Storage container name or CosmosDB container name to use.",
        default=None,
    )
    account_url: str | None = Field(
        description="The account url for Azure services.",
        default=None,
    )
    database_name: str | None = Field(
        description="The database name to use.",
        default=None,
    )
