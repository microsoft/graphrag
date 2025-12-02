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
        description="The storage type to use.",
        default=StorageType.FILE,
    )

    encoding: str | None = Field(
        description="The encoding to use for file storage.",
        default=None,
    )

    base_dir: str | None = Field(
        description="The base directory for the output.",
        default=None,
    )

    connection_string: str | None = Field(
        description="The storage connection string to use.",
        default=None,
    )

    container_name: str | None = Field(
        description="The storage container name to use.",
        default=None,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=None,
    )
    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url to use.",
        default=None,
    )
