# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing load_cache method definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from graphrag.index.config import (
    PipelineBlobCacheConfig,
    PipelineCacheType,
    PipelineFileCacheConfig,
)
from graphrag.index.storage import BlobPipelineStorage, FilePipelineStorage

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
        case PipelineCacheType.none:
            return NoopPipelineCache()
        case PipelineCacheType.memory:
            return create_memory_cache()
        case PipelineCacheType.file:
            config = cast(PipelineFileCacheConfig, config)
            storage = FilePipelineStorage(root_dir).child(config.base_dir)
            return JsonPipelineCache(storage)
        case PipelineCacheType.blob:
            config = cast(PipelineBlobCacheConfig, config)
            storage = BlobPipelineStorage(
                config.connection_string, config.container_name, config.base_dir
            )
            return JsonPipelineCache(storage)
        case _:
            msg = f"Unknown cache type: {config.type}"
            raise ValueError(msg)
