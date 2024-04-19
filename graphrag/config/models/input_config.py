# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import (
    DEFAULT_INPUT_BASE_DIR,
    DEFAULT_INPUT_CSV_PATTERN,
    DEFAULT_INPUT_FILE_ENCODING,
    DEFAULT_INPUT_STORAGE_TYPE,
    DEFAULT_INPUT_TEXT_COLUMN,
    DEFAULT_INPUT_TYPE,
)
from graphrag.config.enums import InputType, StorageType


class InputConfig(BaseModel):
    """The default configuration section for Input."""

    type: InputType = Field(
        description="The input type to use.", default=DEFAULT_INPUT_TYPE
    )
    storage_type: StorageType = Field(
        description="The input storage type to use.", default=DEFAULT_INPUT_STORAGE_TYPE
    )
    base_dir: str = Field(
        description="The input base directory to use.", default=DEFAULT_INPUT_BASE_DIR
    )
    connection_string: str | None = Field(
        description="The azure blob storage connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The azure blob storage container name to use.", default=None
    )
    file_encoding: str | None = Field(
        description="The input file encoding to use.",
        default=DEFAULT_INPUT_FILE_ENCODING,
    )
    file_pattern: str = Field(
        description="The input file pattern to use.", default=DEFAULT_INPUT_CSV_PATTERN
    )
    source_column: str | None = Field(
        description="The input source column to use.", default=None
    )
    timestamp_column: str | None = Field(
        description="The input timestamp column to use.", default=None
    )
    timestamp_format: str | None = Field(
        description="The input timestamp format to use.", default=None
    )
    text_column: str = Field(
        description="The input text column to use.", default=DEFAULT_INPUT_TEXT_COLUMN
    )
    title_column: str | None = Field(
        description="The input title column to use.", default=None
    )
    document_attribute_columns: list[str] = Field(
        description="The document attribute columns to use.", default=[]
    )
