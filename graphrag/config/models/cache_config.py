# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import CacheType


class CacheConfig(BaseModel):
    """The default configuration section for Cache."""

    type: CacheType = Field(
        description="The cache type to use.", default=defs.CACHE_TYPE
    )
    base_dir: str = Field(
        description="The base directory for the cache.", default=defs.CACHE_BASE_DIR
    )
    connection_string: str | None = Field(
        description="The cache connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The cache container name to use.", default=None
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.", default=None
    )
