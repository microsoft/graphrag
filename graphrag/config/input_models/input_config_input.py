# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict

from graphrag.config.enums import InputFileType, InputType


class InputConfigInput(TypedDict):
    """The default configuration section for Input."""

    type: NotRequired[InputType | str | None]
    file_type: NotRequired[InputFileType | str | None]
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
    storage_account_blob_url: NotRequired[str | None]
