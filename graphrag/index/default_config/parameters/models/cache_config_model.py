# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.config import PipelineCacheType


class CacheConfigModel(BaseModel):
    """The default configuration section for Cache."""

    type: PipelineCacheType | None = Field(
        description="The cache type to use.", default=None
    )
    base_dir: str | None = Field(
        description="The base directory for the cache.", default=None
    )
    connection_string: str | None = Field(
        description="The cache connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The cache container name to use.", default=None
    )
