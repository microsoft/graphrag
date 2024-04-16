# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing import TypedDict

from typing_extensions import NotRequired

from graphrag.index.config import PipelineInputStorageType, PipelineInputType


class InputConfigInputModel(TypedDict):
    """The default configuration section for Input."""

    type: NotRequired[PipelineInputType | str | None]
    storage_type: NotRequired[PipelineInputStorageType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
    file_encoding: NotRequired[str | None]
    file_pattern: NotRequired[str | None]
    source_column: NotRequired[str | None]
    timestamp_column: NotRequired[str | None]
    timestamp_format: NotRequired[str | None]
    text_column: NotRequired[str | None]
    title_column: NotRequired[str | None]
    document_attribute_columns: NotRequired[list[str] | str | None]
