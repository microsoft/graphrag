# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from graphrag_storage import StorageConfig
from pydantic import BaseModel, ConfigDict, Field

from graphrag_input.input_file_type import InputFileType


class InputConfig(BaseModel):
    """The default configuration section for Input."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom reader implementations."""

    storage: StorageConfig = Field(
        description="The storage configuration to use for reading input documents.",
        default_factory=lambda: StorageConfig(base_dir="input"),
    )
    file_type: str = Field(
        description="The input file type to use.",
        default=InputFileType.Text,
    )
    encoding: str | None = Field(
        description="The input file encoding to use.",
        default=None,
    )
    file_pattern: str | None = Field(
        description="The input file pattern to use.",
        default=None,
    )
    id_column: str | None = Field(
        description="The input ID column to use.",
        default=None,
    )
    title_column: str | None = Field(
        description="The input title column to use.",
        default=None,
    )
    text_column: str | None = Field(
        description="The input text column to use.",
        default=None,
    )
