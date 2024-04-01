#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration."""
from pydantic import BaseModel, Field

from graphrag.index.config import PipelineStorageType


class StorageConfigModel(BaseModel):
    """The default configuration section for Storage."""

    type: PipelineStorageType | None = Field(
        description="The storage type to use.", default=None
    )
    base_dir: str | None = Field(
        description="The base directory for the storage.", default=None
    )
    connection_string: str | None = Field(
        description="The storage connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The storage container name to use.", default=None
    )
