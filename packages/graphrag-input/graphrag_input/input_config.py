# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_input.input_type import InputType


class InputConfig(BaseModel):
    """The default configuration section for Input."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom reader implementations."""

    type: str = Field(
        description="The input file type to use.",
        default=InputType.Text,
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
