# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing 'PipelineStorageConfig', 'PipelineFileStorageConfig' and 'PipelineMemoryStorageConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from graphrag.config.enums import PipelineStorageType

T = TypeVar("T")


class PipelineStorageConfig(BaseModel, Generic[T]):
    """Represent the storage configuration for the pipeline."""

    type: T


class PipelineFileStorageConfig(
    PipelineStorageConfig[Literal[PipelineStorageType.file]]
):
    """Represent the file storage configuration for the pipeline."""

    type: Literal[PipelineStorageType.file] = PipelineStorageType.file
    """The type of storage."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the storage.", default=None
    )
    """The base directory for the storage."""


class PipelineMemoryStorageConfig(
    PipelineStorageConfig[Literal[PipelineStorageType.memory]]
):
    """Represent the memory storage configuration for the pipeline."""

    type: Literal[PipelineStorageType.memory] = PipelineStorageType.memory
    """The type of storage."""


class PipelineBlobStorageConfig(
    PipelineStorageConfig[Literal[PipelineStorageType.blob]]
):
    """Represents the blob storage configuration for the pipeline."""

    type: Literal[PipelineStorageType.blob] = PipelineStorageType.blob
    """The type of storage."""

    connection_string: str = pydantic_Field(
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


PipelineStorageConfigTypes = (
    PipelineFileStorageConfig | PipelineMemoryStorageConfig | PipelineBlobStorageConfig
)
