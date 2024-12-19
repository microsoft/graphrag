# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineStorageConfig', 'PipelineFileStorageConfig','PipelineMemoryStorageConfig', 'PipelineBlobStorageConfig', and 'PipelineCosmosDBStorageConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from graphrag.config.enums import StorageType

T = TypeVar("T")


class PipelineStorageConfig(BaseModel, Generic[T]):
    """Represent the storage configuration for the pipeline."""

    type: T


class PipelineFileStorageConfig(PipelineStorageConfig[Literal[StorageType.file]]):
    """Represent the file storage configuration for the pipeline."""

    type: Literal[StorageType.file] = StorageType.file
    """The type of storage."""

    base_dir: str | None = Field(
        description="The base directory for the storage.", default=None
    )
    """The base directory for the storage."""


class PipelineMemoryStorageConfig(PipelineStorageConfig[Literal[StorageType.memory]]):
    """Represent the memory storage configuration for the pipeline."""

    type: Literal[StorageType.memory] = StorageType.memory
    """The type of storage."""


class PipelineBlobStorageConfig(PipelineStorageConfig[Literal[StorageType.blob]]):
    """Represents the blob storage configuration for the pipeline."""

    type: Literal[StorageType.blob] = StorageType.blob
    """The type of storage."""

    connection_string: str | None = Field(
        description="The blob storage connection string for the storage.", default=None
    )
    """The blob storage connection string for the storage."""

    container_name: str = Field(
        description="The container name for storage", default=""
    )
    """The container name for storage."""

    base_dir: str | None = Field(
        description="The base directory for the storage.", default=None
    )
    """The base directory for the storage."""

    storage_account_blob_url: str | None = Field(
        description="The storage account blob url.", default=None
    )
    """The storage account blob url."""


class PipelineCosmosDBStorageConfig(
    PipelineStorageConfig[Literal[StorageType.cosmosdb]]
):
    """Represents the cosmosdb storage configuration for the pipeline."""

    type: Literal[StorageType.cosmosdb] = StorageType.cosmosdb
    """The type of storage."""

    connection_string: str | None = Field(
        description="The cosmosdb storage primary key for the storage.", default=None
    )
    """The cosmosdb storage primary key for the storage."""

    container_name: str = Field(
        description="The container name for storage", default=""
    )
    """The container name for storage."""

    base_dir: str | None = Field(
        description="The base directory for the storage.", default=None
    )
    """The base directory for the storage."""

    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url.", default=None
    )
    """The cosmosdb account url."""


PipelineStorageConfigTypes = (
    PipelineFileStorageConfig
    | PipelineMemoryStorageConfig
    | PipelineBlobStorageConfig
    | PipelineCosmosDBStorageConfig
)
