# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cache configuration model."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_cache.cache_type import CacheType


class CacheConfig(BaseModel):
    """The configuration section for cache."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom cache implementations."""

    type: str = Field(
        description="The cache type to use. Builtin types include 'Json', 'Memory', and 'Noop'.",
        default=CacheType.Json,
    )

    encoding: str | None = Field(
        description="The encoding to use for file-based caching.",
        default=None,
    )

    name: str | None = Field(
        description="The name to use for the cache instance.",
        default=None,
    )
