# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cache functions for the GraphRAG update module."""

from graphrag.index.cache.load_cache import load_cache
from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.config.cache import (
    PipelineCacheConfigTypes,
    PipelineMemoryCacheConfig,
)


def _create_cache(
    config: PipelineCacheConfigTypes | None, root_dir: str
) -> PipelineCache:
    return load_cache(config or PipelineMemoryCacheConfig(), root_dir=root_dir)
