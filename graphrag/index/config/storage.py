# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineStorageConfig', 'PipelineFileStorageConfig' and 'PipelineMemoryStorageConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from graphrag.config.enums import StorageType

T = TypeVar("T")


class PipelineStorageConfig(BaseModel, Generic[T]):
    """Represent the storage configuration for the pipeline."""

    type: T


class PipelineFileStorageConfig(PipelineStorageConfig[Literal[StorageType.file]]):
    """Represent the file storage configuration for the pipeline."""

    type: Literal[StorageType.file] = StorageType.file
    """The type of storage."""

    base_dir: str | None = pydantic_Field(
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

    connection_string: str | None = pydantic_Field(
        description="The blob storage connection string for the storage.", default=None
    )
    """The blob storage connection string for the storage."""

    container_name: str = pydantic_Field(
        description="The container name for storage", default=None
    )
    """The container name for storage."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the storage.", default=None
    )
    """The base directory for the storage."""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url.", default=None
    )
    """The storage account blob url."""


PipelineStorageConfigTypes = (
    PipelineFileStorageConfig | PipelineMemoryStorageConfig | PipelineBlobStorageConfig
)
