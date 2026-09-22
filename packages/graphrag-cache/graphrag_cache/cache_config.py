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
        description="The cache type to use. Builtin types include 'Json', 'Memory', 'Noop', and 'Sqlite'.",
        default=CacheType.Json,
    )

    storage: StorageConfig | None = Field(
        description="The storage configuration to use for storage-backed caches such as 'Json' and 'Sqlite'.",
        default_factory=lambda: StorageConfig(type=StorageType.File, base_dir="cache"),
    )

    database_name: str = Field(
        description="The SQLite database name within the configured file storage. Used only when type is 'Sqlite'.",
        default="cache.db",
    )
