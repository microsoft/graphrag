# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import StorageType


class StorageConfig(BaseModel):
    """The default configuration section for storage."""

    type: StorageType = Field(
        description="The storage type to use.",
        default=graphrag_config_defaults.storage.type,
    )
    base_dir: str = Field(
        description="The base directory for the output.",
        default=graphrag_config_defaults.storage.base_dir,
    )
    connection_string: str | None = Field(
        description="The storage connection string to use.",
        default=graphrag_config_defaults.storage.connection_string,
    )
    container_name: str | None = Field(
        description="The storage container name to use.",
        default=graphrag_config_defaults.storage.container_name,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=graphrag_config_defaults.storage.storage_account_blob_url,
    )
    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url to use.",
        default=graphrag_config_defaults.storage.cosmosdb_account_url,
    )
