# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineCacheConfig', 'PipelineFileCacheConfig', 'PipelineMemoryCacheConfig', 'PipelineBlobCacheConfig', 'PipelineCosmosDBCacheConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from graphrag.config.enums import CacheType

T = TypeVar("T")


class PipelineCacheConfig(BaseModel, Generic[T]):
    """Represent the cache configuration for the pipeline."""

    type: T


class PipelineFileCacheConfig(PipelineCacheConfig[Literal[CacheType.file]]):
    """Represent the file cache configuration for the pipeline."""

    type: Literal[CacheType.file] = CacheType.file
    """The type of cache."""

    base_dir: str | None = Field(
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

    base_dir: str | None = Field(
        description="The base directory for the cache.", default=None
    )
    """The base directory for the cache."""

    connection_string: str | None = Field(
        description="The blob cache connection string for the cache.", default=None
    )
    """The blob cache connection string for the cache."""

    container_name: str = Field(description="The container name for cache", default="")
    """The container name for cache"""

    storage_account_blob_url: str | None = Field(
        description="The storage account blob url for cache", default=None
    )
    """The storage account blob url for cache"""


class PipelineCosmosDBCacheConfig(PipelineCacheConfig[Literal[CacheType.cosmosdb]]):
    """Represents the cosmosdb cache configuration for the pipeline."""

    type: Literal[CacheType.cosmosdb] = CacheType.cosmosdb
    """The type of cache."""

    base_dir: str | None = Field(
        description="The cosmosdb database name for the cache.", default=None
    )
    """The cosmosdb database name for the cache."""

    container_name: str = Field(description="The container name for cache.", default="")
    """The container name for cache."""

    connection_string: str | None = Field(
        description="The cosmosdb primary key for the cache.", default=None
    )
    """The cosmosdb primary key for the cache."""

    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url for cache", default=None
    )
    """The cosmosdb account url for cache"""


PipelineCacheConfigTypes = (
    PipelineFileCacheConfig
    | PipelineMemoryCacheConfig
    | PipelineBlobCacheConfig
    | PipelineNoneCacheConfig
    | PipelineCosmosDBCacheConfig
)
