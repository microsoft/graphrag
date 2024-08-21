# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import StorageType


class StorageConfig(BaseModel):
    """The default configuration section for Storage."""

    type: StorageType = Field(
        description="The storage type to use.", default=defs.STORAGE_TYPE
    )
    base_dir: str = Field(
        description="The base directory for the storage.",
        default=defs.STORAGE_BASE_DIR,
    )
    connection_string: str | None = Field(
        description="The storage connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The storage container name to use.", default=None
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.", default=None
    )
    bucket_name: str| None = Field(
        description="The bucket name for the input files.", default=None
    )
    """The bucket name for the input files."""
    access_key: str| None = Field(
        description="The access key  for the input files.", default=None
    )
    """The access key for the input files."""
    secret_key: str| None = Field(
        description="The secret key for the input files.", default=None
    )
    """The secret key for the input files."""
    endpoint: str | None = Field(
        description="The endpoint for the input files.", default=None
    )
    """The endpoint for the input files."""