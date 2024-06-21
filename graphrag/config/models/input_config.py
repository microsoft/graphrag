# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import InputFileType, InputType


class InputConfig(BaseModel):
    """The default configuration section for Input."""

    type: InputType = Field(
        description="The input type to use.", default=defs.INPUT_TYPE
    )
    file_type: InputFileType = Field(
        description="The input file type to use.", default=defs.INPUT_FILE_TYPE
    )
    base_dir: str = Field(
        description="The input base directory to use.", default=defs.INPUT_BASE_DIR
    )
    connection_string: str | None = Field(
        description="The azure blob storage connection string to use.", default=None
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.", default=None
    )
    container_name: str | None = Field(
        description="The azure blob storage container name to use.", default=None
    )
    encoding: str | None = Field(
        description="The input file encoding to use.",
        default=defs.INPUT_FILE_ENCODING,
    )
    file_pattern: str = Field(
        description="The input file pattern to use.", default=defs.INPUT_TEXT_PATTERN
    )
    file_filter: dict[str, str] | None = Field(
        description="The optional file filter for the input files.", default=None
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
        description="The input text column to use.", default=defs.INPUT_TEXT_COLUMN
    )
    title_column: str | None = Field(
        description="The input title column to use.", default=None
    )
    document_attribute_columns: list[str] = Field(
        description="The document attribute columns to use.", default=[]
    )
