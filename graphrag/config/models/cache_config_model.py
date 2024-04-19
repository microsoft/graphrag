# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import (
    DEFAULT_CACHE_BASE_DIR,
    DEFAULT_CACHE_TYPE,
)
from graphrag.config.enums import PipelineCacheType


class CacheConfigModel(BaseModel):
    """The default configuration section for Cache."""

    type: PipelineCacheType = Field(
        description="The cache type to use.", default=DEFAULT_CACHE_TYPE
    )
    base_dir: str = Field(
        description="The base directory for the cache.", default=DEFAULT_CACHE_BASE_DIR
    )
    connection_string: str | None = Field(
        description="The cache connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The cache container name to use.", default=None
    )
