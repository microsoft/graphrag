# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cache configuration model."""

from graphrag_storage import StorageConfig, StorageType
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

    storage: StorageConfig | None = Field(
        description="The storage configuration to use for file-based caches such as 'Json'.",
        default_factory=lambda: StorageConfig(type=StorageType.File, base_dir="cache"),
    )
