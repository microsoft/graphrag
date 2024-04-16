# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing import TypedDict

from typing_extensions import NotRequired

from graphrag.index.config import PipelineStorageType


class StorageConfigInputModel(TypedDict):
    """The default configuration section for Storage."""

    type: NotRequired[PipelineStorageType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
