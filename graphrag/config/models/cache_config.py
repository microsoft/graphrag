# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import CacheType


class CacheConfig(BaseModel):
    """The default configuration section for Cache."""

    type: CacheType = Field(
        description="The cache type to use.",
        default=graphrag_config_defaults.cache.type,
    )
    base_dir: str = Field(
        description="The base directory for the cache.",
        default=graphrag_config_defaults.cache.base_dir,
    )
    connection_string: str | None = Field(
        description="The cache connection string to use.",
        default=graphrag_config_defaults.cache.connection_string,
    )
    container_name: str | None = Field(
        description="The cache container name to use.",
        default=graphrag_config_defaults.cache.container_name,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=graphrag_config_defaults.cache.storage_account_blob_url,
    )
    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url to use.",
        default=graphrag_config_defaults.cache.cosmosdb_account_url,
    )
