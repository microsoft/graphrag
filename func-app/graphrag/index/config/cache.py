# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineCacheConfig', 'PipelineFileCacheConfig' and 'PipelineMemoryCacheConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from graphrag.config.enums import CacheType

T = TypeVar("T")


class PipelineCacheConfig(BaseModel, Generic[T]):
    """Represent the cache configuration for the pipeline."""

    type: T


class PipelineFileCacheConfig(PipelineCacheConfig[Literal[CacheType.file]]):
    """Represent the file cache configuration for the pipeline."""

    type: Literal[CacheType.file] = CacheType.file
    """The type of cache."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """The base directory for the cache."""


class PipelineMemoryCacheConfig(PipelineCacheConfig[Literal[CacheType.memory]]):
    """Represent the memory cache configuration for the pipeline."""

    type: Literal[CacheType.memory] = CacheType.memory
    """The type of cache."""


class PipelineNoneCacheConfig(PipelineCacheConfig[Literal[CacheType.none]]):
    """Represent the none cache configuration for the pipeline."""

    type: Literal[CacheType.none] = CacheType.none
    """The type of cache."""


class PipelineBlobCacheConfig(PipelineCacheConfig[Literal[CacheType.blob]]):
    """Represents the blob cache configuration for the pipeline."""

    type: Literal[CacheType.blob] = CacheType.blob
    """The type of cache."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the cache.", default=None
    )
    """The base directory for the cache."""

    connection_string: str | None = pydantic_Field(
        description="The blob cache connection string for the cache.", default=None
    )
    """The blob cache connection string for the cache."""

    container_name: str = pydantic_Field(
        description="The container name for cache", default=None
    )
    """The container name for cache"""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url for cache", default=None
    )
    """The storage account blob url for cache"""


PipelineCacheConfigTypes = (
    PipelineFileCacheConfig
    | PipelineMemoryCacheConfig
    | PipelineBlobCacheConfig
    | PipelineNoneCacheConfig
)
