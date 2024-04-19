# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import (
    DEFAULT_STORAGE_BASE_DIR,
    DEFAULT_STORAGE_TYPE,
)
from graphrag.config.enums import StorageType


class StorageConfig(BaseModel):
    """The default configuration section for Storage."""

    type: StorageType = Field(
        description="The storage type to use.", default=DEFAULT_STORAGE_TYPE
    )
    base_dir: str = Field(
        description="The base directory for the storage.",
        default=DEFAULT_STORAGE_BASE_DIR,
    )
    connection_string: str | None = Field(
        description="The storage connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The storage container name to use.", default=None
    )
