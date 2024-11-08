# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load_cache method definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from graphrag.config.enums import CacheType
from graphrag.index.config.cache import (
    PipelineBlobCacheConfig,
    PipelineCosmosDBCacheConfig,
    PipelineFileCacheConfig,
)
from graphrag.index.storage import (
    BlobPipelineStorage,
    FilePipelineStorage,
    create_cosmosdb_storage,
)

if TYPE_CHECKING:
    from graphrag.index.config import (
        PipelineCacheConfig,
    )

from .json_pipeline_cache import JsonPipelineCache
from .memory_pipeline_cache import create_memory_cache
from .noop_pipeline_cache import NoopPipelineCache


def load_cache(config: PipelineCacheConfig | None, root_dir: str | None):
    """Load the cache from the given config."""
    if config is None:
        return NoopPipelineCache()

    match config.type:
        case CacheType.none:
            return NoopPipelineCache()
        case CacheType.memory:
            return create_memory_cache()
        case CacheType.file:
            config = cast(PipelineFileCacheConfig, config)
            storage = FilePipelineStorage(root_dir).child(config.base_dir)
            return JsonPipelineCache(storage)
        case CacheType.blob:
            config = cast(PipelineBlobCacheConfig, config)
            storage = BlobPipelineStorage(
                config.connection_string,
                config.container_name,
                storage_account_blob_url=config.storage_account_blob_url,
            ).child(config.base_dir)
            return JsonPipelineCache(storage)
        case CacheType.cosmosdb:
            config = cast(PipelineCosmosDBCacheConfig, config)
            storage = create_cosmosdb_storage(
                cosmosdb_account_url=config.cosmosdb_account_url,
                connection_string=config.connection_string,
                container_name=None,
                base_dir=config.base_dir,
            )
            return JsonPipelineCache(storage)
        case _:
            msg = f"Unknown cache type: {config.type}"
            raise ValueError(msg)
