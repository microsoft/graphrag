#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing 'PipelineCacheConfig', 'PipelineFileCacheConfig' and 'PipelineMemoryCacheConfig' models."""
from __future__ import annotations

from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field


class PipelineCacheType(str, Enum):
    """Represent the cache configuration type for the pipeline."""

    file = "file"
    """The file cache configuration type."""
    memory = "memory"
    """The memory cache configuration type."""
    none = "none"
    """The none cache configuration type."""
    blob = "blob"
    """The blob cache configuration type."""


T = TypeVar("T")


class PipelineCacheConfig(BaseModel, Generic[T]):
    """Represent the cache configuration for the pipeline."""

    type: T


class PipelineFileCacheConfig(PipelineCacheConfig[Literal[PipelineCacheType.file]]):
    """Represent the file cache configuration for the pipeline."""

    type: Literal[PipelineCacheType.file] = PipelineCacheType.file
    """The type of cache."""
    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """The base directory for the cache."""


class PipelineMemoryCacheConfig(PipelineCacheConfig[Literal[PipelineCacheType.memory]]):
    """Represent the memory cache configuration for the pipeline."""

    type: Literal[PipelineCacheType.memory] = PipelineCacheType.memory
    """The type of cache."""


class PipelineNoneCacheConfig(PipelineCacheConfig[Literal[PipelineCacheType.none]]):
    """Represent the none cache configuration for the pipeline."""

    type: Literal[PipelineCacheType.none] = PipelineCacheType.none
    """The type of cache."""


class PipelineBlobCacheConfig(PipelineCacheConfig[Literal[PipelineCacheType.blob]]):
    """Represents the blob cache configuration for the pipeline."""

    type: Literal[PipelineCacheType.blob] = PipelineCacheType.blob
    """The type of cache."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """The base directory for the cache."""

    connection_string: str = pydantic_Field(
        description="The blob cache connection string for the cache.", default=None
    )
    """The blob cache connection string for the cache."""

    container_name: str = pydantic_Field(
        description="The container name for cache", default=None
    )
    """The container name for cache"""


PipelineCacheConfigTypes = (
    PipelineFileCacheConfig
    | PipelineMemoryCacheConfig
    | PipelineBlobCacheConfig
    | PipelineNoneCacheConfig
)
