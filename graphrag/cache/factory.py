# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_cache method definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from graphrag.config.enums import CacheType
from graphrag.index.config.cache import (
    PipelineBlobCacheConfig,
    PipelineFileCacheConfig,
)
from graphrag.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage

if TYPE_CHECKING:
    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.index.config.cache import (
        PipelineCacheConfig,
    )

from graphrag.cache.json_pipeline_cache import JsonPipelineCache
from graphrag.cache.memory_pipeline_cache import InMemoryCache
from graphrag.cache.noop_pipeline_cache import NoopPipelineCache


def create_cache(
    config: PipelineCacheConfig | None, root_dir: str | None
) -> PipelineCache:
    """Create a cache from the given config."""
    if config is None:
        return NoopPipelineCache()

    match config.type:
        case CacheType.none:
            return NoopPipelineCache()
        case CacheType.memory:
            return InMemoryCache()
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
        case _:
            msg = f"Unknown cache type: {config.type}"
            raise ValueError(msg)
